from models import Usuario, Curriculo
from fastapi import FastAPI, Request, Form, Depends, APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
from models import Curriculo
from auth import hash_senha, verificar_senha, validar_forca_senha, gerar_senha_temporaria
from ia import processar_curriculo

import json
import os
import shutil

# =========================
# BASE DIR
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# =========================
# APP
# =========================
app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# INICIALIZAÇÃO DO BANCO
# =========================
models.Base.metadata.create_all(bind=engine)

# =========================
# ROUTER
# =========================
router = APIRouter()

# =========================
# DB
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# ROTAS PÚBLICAS
# =========================

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(request: Request, email: str = Form(...), senha: str = Form(...), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()

    if usuario:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "erro": "Usuário já existe"
        })

    valida, msg = validar_forca_senha(senha)
    if not valida:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "erro": msg
        })

    novo_usuario = models.Usuario(
        email=email,
        senha=hash_senha(senha)
    )

    db.add(novo_usuario)
    db.commit()

    return RedirectResponse(url="/login", status_code=302)

@router.post("/login")
def login(request: Request, email: str = Form(...), senha: str = Form(...), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()

    if not usuario or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "erro": "Login inválido"
        })

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="user_id", value=str(usuario.id))
    return response

@router.get("/recuperar", response_class=HTMLResponse)
def recuperar_page(request: Request):
    return templates.TemplateResponse("recuperar.html", {"request": request})

@router.post("/recuperar")
def recuperar_senha(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()

    if not usuario:
        return templates.TemplateResponse("recuperar.html", {
            "request": request,
            "erro": "Email não encontrado"
        })

    nova_senha = gerar_senha_temporaria()
    usuario.senha = hash_senha(nova_senha)
    db.commit()

    return templates.TemplateResponse("recuperar.html", {
        "request": request,
        "sucesso": f"Sua nova senha é: {nova_senha}"
    })

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("user_id")
    return response

# =========================
# ROTAS PROTEGIDAS
# =========================

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()

    if not usuario:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == usuario.id).first()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": usuario,
        "curriculo": curriculo,
        "pago": True
    })

@router.get("/criar-curriculo", response_class=HTMLResponse)
def pagina_criar(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    existente = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if existente:
        return RedirectResponse(url="/dashboard")

    return templates.TemplateResponse("criar_curriculo.html", {"request": request})

@router.post("/criar-curriculo")
def criar_curriculo(
    request: Request,
    texto: str = Form(...),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    dados_tratados = processar_curriculo(texto)
    
    if not dados_tratados:
        return templates.TemplateResponse("criar_curriculo.html", {
            "request": request,
            "erro": "Erro ao processar currículo. Tente novamente."
        })

    caminho_foto = None
    if foto and foto.filename:
        os.makedirs("static/fotos", exist_ok=True)
        temp_path = os.path.join("static", "fotos", f"temp_{user_id}_{foto.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        caminho_foto = temp_path

    novo = Curriculo(
        user_id=int(user_id),
        dados_brutos=texto,
        dados_tratados=json.dumps(dados_tratados) if dados_tratados else None,
        foto=caminho_foto
    )

    db.add(novo)
    db.commit()

    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/editar-curriculo", response_class=HTMLResponse)
def editar_curriculo(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/criar-curriculo")

    return templates.TemplateResponse("editar_curriculo.html", {
        "request": request,
        "curriculo": curriculo
    })

@router.post("/editar-curriculo")
def salvar_edicao(
    request: Request,
    dados_brutos: str = Form(...),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/dashboard")

    dados_novos = processar_curriculo(dados_brutos)
    
    if not dados_novos:
        return templates.TemplateResponse("editar_curriculo.html", {
            "request": request,
            "curriculo": curriculo,
            "erro": "Erro ao processar currículo. Tente novamente."
        })

    try:
        dados_antigos = json.loads(curriculo.dados_tratados) if curriculo.dados_tratados else {}
        if dados_antigos:
            if "nome" in dados_antigos and dados_antigos["nome"]:
                dados_novos["nome"] = dados_antigos["nome"]
            if "resumo" in dados_antigos and dados_antigos["resumo"]:
                dados_novos["resumo"] = dados_antigos["resumo"]
    except Exception as e:
        print("Erro ao manter dados antigos:", e)

    if foto and foto.filename:
        os.makedirs("static/fotos", exist_ok=True)
        caminho_foto = os.path.join("static", "fotos", f"user_{user_id}_{foto.filename}")
        with open(caminho_foto, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        curriculo.foto = caminho_foto

    curriculo.dados_brutos = dados_brutos
    curriculo.dados_tratados = json.dumps(dados_novos) if dados_novos else None
    db.commit()

    return RedirectResponse(url="/dashboard", status_code=302)

# =========================
# PREVIEW E MODELOS
# =========================

@router.get("/preview")
def preview(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/dashboard")

    try:
        dados = json.loads(curriculo.dados_tratados) if curriculo.dados_tratados else {}
    except:
        return RedirectResponse(url="/dashboard")

    modelo = curriculo.modelo or 1

    if modelo == 2:
        template = "preview_modelo2.html"
    elif modelo == 3:
        template = "preview_modelo3.html"
    elif modelo == 4:
        template = "preview_modelo4.html"
    else:
        template = "preview.html"

    return templates.TemplateResponse(template, {
        "request": request,
        "dados": dados,
        "curriculo": curriculo
    })

@router.get("/preview_modelo2")
def preview_modelo2(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/dashboard")

    dados = json.loads(curriculo.dados_tratados) if curriculo.dados_tratados else {}

    return templates.TemplateResponse("preview_modelo2.html", {
        "request": request,
        "dados": dados,
        "curriculo": curriculo
    })

@router.get("/preview_modelo3")
def preview_modelo3(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/dashboard")

    dados = json.loads(curriculo.dados_tratados) if curriculo.dados_tratados else {}

    return templates.TemplateResponse("preview_modelo3.html", {
        "request": request,
        "dados": dados,
        "curriculo": curriculo
    })

@router.get("/preview_modelo4")
def preview_modelo4(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/dashboard")

    dados = json.loads(curriculo.dados_tratados) if curriculo.dados_tratados else {}

    return templates.TemplateResponse("preview_modelo4.html", {
        "request": request,
        "dados": dados,
        "curriculo": curriculo
    })

@router.get("/salvar_modelo/{modelo}")
def salvar_modelo(modelo: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/")

    curriculo = db.query(Curriculo).filter(Curriculo.user_id == int(user_id)).first()

    if not curriculo:
        return RedirectResponse(url="/dashboard")

    curriculo.modelo = modelo
    db.commit()

    return RedirectResponse(url="/dashboard")

# =========================
# PLANOS E PAGAMENTO
# =========================

@router.get("/planos", response_class=HTMLResponse)
def planos(request: Request):
    return templates.TemplateResponse("planos.html", {"request": request})

@router.get("/assinar")
def assinar():
    return RedirectResponse(url="/pagamento")

@router.get("/pagamento", response_class=HTMLResponse)
def pagamento(request: Request):
    return templates.TemplateResponse("pagamento.html", {"request": request})

@router.get("/preview-check")
def preview_check(request: Request):
    pago = request.cookies.get("pago") == "true"

    if not pago:
        return RedirectResponse(url="/pagamento")

    return RedirectResponse(url="/preview")

@router.get("/liberar")
def liberar():
    response = RedirectResponse(url="/preview")
    response.set_cookie(key="pago", value="true")
    return response

# =========================
# INCLUI ROUTER NO APP
# =========================
app.include_router(router)