from datetime import datetime

from flask import Flask, abort, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "eduvesp-dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///educonecta.db"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar esta página."
login_manager.login_message_category = "warning"


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)  # professor | pai | aluno
    comunicados = db.relationship("Comunicado", backref="autor", lazy=True)


class Comunicado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    comentarios = db.relationship("Comentario", backref="comunicado", lazy=True, order_by="Comentario.criado_em")


class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    comunicado_id = db.Column(db.Integer, db.ForeignKey("comunicado.id"), nullable=False)
    autor = db.relationship("Usuario")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    erro = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]
        usuario = db.session.execute(
            db.select(Usuario).filter_by(email=email)
        ).scalar_one_or_none()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            login_user(usuario)
            return redirect(url_for("dashboard"))
        erro = "Email ou senha inválidos."
    return render_template("login.html", erro=erro)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    erro = None
    if request.method == "POST":
        nome = request.form["nome"].strip()
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]
        perfil = request.form["perfil"]
        if perfil not in ("professor", "pai", "aluno"):
            erro = "Perfil inválido."
        elif db.session.execute(
            db.select(Usuario).filter_by(email=email)
        ).scalar_one_or_none():
            erro = "Este email já está cadastrado."
        else:
            usuario = Usuario(
                nome=nome,
                email=email,
                senha_hash=generate_password_hash(senha),
                perfil=perfil,
            )
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            return redirect(url_for("dashboard"))
    return render_template("registro.html", erro=erro)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    comunicados = db.session.execute(
        db.select(Comunicado).order_by(Comunicado.criado_em.desc())
    ).scalars().all()
    return render_template("dashboard.html", comunicados=comunicados)


@app.route("/comunicados/novo", methods=["GET", "POST"])
@login_required
def novo_comunicado():
    if current_user.perfil != "professor":
        abort(403)
    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        conteudo = request.form["conteudo"].strip()
        comunicado = Comunicado(
            titulo=titulo, conteudo=conteudo, autor_id=current_user.id
        )
        db.session.add(comunicado)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("novo_comunicado.html")


@app.route("/comunicados/<int:comunicado_id>/editar", methods=["GET", "POST"])
@login_required
def editar_comunicado(comunicado_id):
    comunicado = db.session.get(Comunicado, comunicado_id)
    if comunicado is None:
        abort(404)
    if current_user.perfil != "professor" or comunicado.autor_id != current_user.id:
        abort(403)
    if request.method == "POST":
        comunicado.titulo = request.form["titulo"].strip()
        comunicado.conteudo = request.form["conteudo"].strip()
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("editar_comunicado.html", comunicado=comunicado)


@app.route("/comunicados/<int:comunicado_id>/excluir", methods=["POST"])
@login_required
def excluir_comunicado(comunicado_id):
    comunicado = db.session.get(Comunicado, comunicado_id)
    if comunicado is None:
        abort(404)
    if current_user.perfil != "professor" or comunicado.autor_id != current_user.id:
        abort(403)
    db.session.delete(comunicado)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/comunicados/<int:comunicado_id>/comentar", methods=["POST"])
@login_required
def comentar(comunicado_id):
    if current_user.perfil != "pai":
        abort(403)
    comunicado = db.session.get(Comunicado, comunicado_id)
    if comunicado is None:
        abort(404)
    conteudo = request.form["conteudo"].strip()
    if conteudo:
        comentario = Comentario(
            conteudo=conteudo,
            autor_id=current_user.id,
            comunicado_id=comunicado_id,
        )
        db.session.add(comentario)
        db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/comentarios/<int:comentario_id>/editar", methods=["GET", "POST"])
@login_required
def editar_comentario(comentario_id):
    comentario = db.session.get(Comentario, comentario_id)
    if comentario is None:
        abort(404)
    if current_user.perfil != "pai" or comentario.autor_id != current_user.id:
        abort(403)
    if request.method == "POST":
        comentario.conteudo = request.form["conteudo"].strip()
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("editar_comentario.html", comentario=comentario)


@app.route("/comentarios/<int:comentario_id>/excluir", methods=["POST"])
@login_required
def excluir_comentario(comentario_id):
    comentario = db.session.get(Comentario, comentario_id)
    if comentario is None:
        abort(404)
    if current_user.perfil != "pai" or comentario.autor_id != current_user.id:
        abort(403)
    db.session.delete(comentario)
    db.session.commit()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
