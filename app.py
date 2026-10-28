from PySide6 import QtWidgets, QtCore
import os 
import sys 
import sqlite3
from datetime import datetime, date
import json


# --------- Banco de Dados ----------

pasta_localData = QtCore.QStandardPaths.writableLocation(
    QtCore.QStandardPaths.StandardLocation.AppDataLocation
)

print(pasta_localData)

os.makedirs(pasta_localData, exist_ok=True)

conexao = sqlite3.connect(os.path.join(pasta_localData, "metas.db"))
cursor = conexao.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    prazo DATE NOT NULL
);
""")

conexao.commit()

# ---------- TELAS ----------

# ---------- Tela Inicial ----------

class tela_inicial(QtWidgets.QWidget):
    
    
    tema_alterado = QtCore.Signal(str)
    
    def __init__(self,stack):
        super().__init__()
        
        self.stack = stack
        
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        
        # ---------- Temas ----------
        
        self.temas = QtWidgets.QComboBox()
        self.temas.addItems(["dark", "light"])
        self.temas.setObjectName("temas")
        self.temas.currentTextChanged.connect(self.tema_alterado.emit)   
        self.layout.addWidget(self.temas, 0, 0)
        
        
        # ---------- Título ----------
        
        self.titulo = QtWidgets.QLabel("Aqui é onde tudo começa !!")
        self.titulo.setObjectName("titulo_inicial")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.titulo, 1, 1, 1 , 2)
        
        # --------- Botão ( Nova Lista) ----------
        
        self.btn_nova_lista = QtWidgets.QPushButton("Nova Lista")
        self.btn_nova_lista.setObjectName("btn_nova_lista")
        self.btn_nova_lista.clicked.connect(self.ir_para_criacao)
        self.layout.addWidget(self.btn_nova_lista, 2, 1, 1, 2) 
        
        # --------- Botão ( Ver Listas ) ----------
        
        self.btn_ver_lista = QtWidgets.QPushButton("Ver Listas")
        self.btn_ver_lista.setObjectName("btn_ver_lista")
        self.btn_ver_lista.clicked.connect(self.ir_para_lista)
        self.layout.addWidget(self.btn_ver_lista, 3, 1)
        
        # --------- Botão ( Importar Lista ) ----------
        
        self.btn_imp_lista = QtWidgets.QPushButton("Importar")
        self.btn_imp_lista.setObjectName("btn_imp_lista")
        self.btn_imp_lista.clicked.connect(self.importar)
        self.layout.addWidget(self.btn_imp_lista, 3, 2)
        
        # --------- Widget de Espaço ----------
        self.espaco = QtWidgets.QWidget()
        self.espaco.setObjectName("espaco")
        self.layout.addWidget(self.espaco, 4, 4)
        
    
    # ---------- Funções ----------
    
    # ---------- Trocar Tela ----------
    
    def ir_para_lista(self):
        self.stack.setCurrentIndex(1)
        
    def ir_para_criacao(self):
        self.stack.setCurrentIndex(3)
        
    # ---------- Importar listas ---------
    
    def importar(self):
        
        try:
            
            caminho, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Pegar lista",
                "",
                "Arquivos JSON (*.json)"
            )
            
            if not caminho:
                return
            
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                
                cursor.execute("SELECT COUNT(*) FROM metas WHERE titulo = ?", (dados["titulo"],))
                
                count = cursor.fetchone()[0]
                
                if not count == 0:
                    QtWidgets.QMessageBox.critical(self, "Erro", "Não poder ter duas tabelas com mesmo titulo")
                    return
                
                cursor.execute("INSERT INTO metas (titulo, prazo) VALUES (?, ?);", (dados["titulo"], dados["prazo"],))
                conexao.commit()
                
                cursor.execute("SELECT id FROM metas WHERE titulo = ?", (dados["titulo"],))
                 
                id_lista = cursor.fetchone()[0]
                
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS lista_{id_lista} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meta TEXT NOT NULL,
                        id_lista INTEGER,
                        estado TEXT DEFAULT 'pendente',
                        FOREIGN KEY (id_lista) REFERENCES metas(id)
                    );
                """)
                
                for meta in dados["metas"]:
                    cursor.execute(f"""
                        INSERT INTO lista_{id_lista} (meta, id_lista, estado) VALUES (?, ?, ?);
                    """, (meta["meta"], id_lista, meta["estado"]))
                
                conexao.commit()
        
        except sqlite3.Error as e:
            QtWidgets.QMessageBox(self, "Erro", f"Erro em importar: {e}")
            return
        
# ---------- Tela Lista ----------

class tela_lista(QtWidgets.QWidget):
    tema_alterado = QtCore.Signal(str)
    lista_atual = QtCore.Signal(int)
    
    def __init__(self, stack):
        super().__init__()
        
        self.stack = stack
        
        self.stack.currentChanged.connect(self.mostrar_lista_metas) 
                    
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        
        # ---------- Título ----------
        
        self.titulo = QtWidgets.QLabel("Todas as suas Metas !!")
        self.titulo.setObjectName("titulo_lista")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.titulo, 1, 1, 1, 2)
        
        # --------- Botão ( Voltar ) ----------
        
        self.btn_voltar = QtWidgets.QPushButton("Voltar")
        self.btn_voltar.setObjectName("btn_voltar")
        self.btn_voltar.clicked.connect(self.voltar_para_inicial)
        self.layout.addWidget(self.btn_voltar, 0, 3)
        
        # --------- Temas ----------
        
        self.temas = QtWidgets.QComboBox()
        self.temas.addItems(["dark", "light"])
        self.temas.setObjectName("temas")
        self.temas.currentTextChanged.connect(self.tema_alterado.emit)
        self.layout.addWidget(self.temas, 0, 0)
        
        # --------- Scroll das listas --------------
        
        self.scroll_lista = QtWidgets.QScrollArea()
        self.scroll_lista.setObjectName("scroll_lista")
        self.scroll_lista.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_lista.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_lista.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scroll_lista.setMinimumHeight(300)
        self.scroll_lista.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_lista, 2, 0, 5, 4)
                
        # --------- Frame ( Lista de Metas ) ----------
        
        self.frame_listas = QtWidgets.QFrame()
        self.frame_listas.setObjectName("frame_listas")
        self.scroll_lista.setWidget(self.frame_listas)
        
        self.layout_listas = QtWidgets.QVBoxLayout(self.frame_listas)
        self.layout_listas.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop)
        
        # ---------- Chamada da função ----------
        
        self.mostrar_lista_metas()
        

    # ---------- Funções ----------
    
    # ---------- Trocar Tela ----------

    def ir_para_metas(self, id_lista):
        self.lista_atual.emit(id_lista)
        self.stack.setCurrentIndex(2)
       

    def voltar_para_inicial(self):
        self.stack.setCurrentIndex(0)
        
    # ---------- Mostrar Lista de Metas ----------
    
    def mostrar_lista_metas(self):
        
        def limpar_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    limpar_layout(item.layout())
        
        try:
            
            cursor.execute("SELECT titulo, id FROM metas;")

            nomes_id_listas = cursor.fetchall()
            
            limpar_layout(self.layout_listas)
                        
            if not nomes_id_listas and self.layout_listas.count() == 0:
                
                self.sem_metas = QtWidgets.QLabel("Nenhuma meta cadastrada.")
                self.sem_metas.setObjectName("sem_metas")
                self.layout_listas.addWidget(self.sem_metas, alignment=QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignTop)
            
            for lista in nomes_id_listas:
                nome_lista = lista[0]
                id_lista = lista[1]

                # --------- Frame ( Metas ) ----------
                        
                self.frame_metas = QtWidgets.QFrame()
                self.frame_metas.setObjectName("frame_metas")
                self.frame_metas.setMaximumHeight(70)
                self.frame_metas.setMaximumWidth(900)
                self.frame_metas.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding,
                    QtWidgets.QSizePolicy.Policy.Minimum,
                )
                self.layout_listas.addWidget(self.frame_metas)
            
                
                self.layout_metas = QtWidgets.QHBoxLayout(self.frame_metas)
                
                # ---------- Botão ( Meta ) ----------
                    
                self.btn_meta = QtWidgets.QPushButton(nome_lista)
                self.btn_meta.setObjectName("btn_meta")
                self.btn_meta.setMaximumHeight(50)
                self.btn_meta.clicked.connect(lambda checked = False, id_lista=id_lista: self.ir_para_metas(id_lista))
                
                self.layout_metas.addWidget(self.btn_meta)
                
                # ---------- Botão ( exportar ) ----------
                
                self.btn_exportar = QtWidgets.QPushButton("Exportar")
                self.btn_exportar.setObjectName("btn_exportar")
                self.btn_exportar.setMaximumHeight(30)
                self.btn_exportar.setMaximumWidth(60)
                self.btn_exportar.clicked.connect(lambda checked = False, id_lista= id_lista: self.exportar(id_lista))
                self.layout_metas.addWidget(self.btn_exportar)
                                
                # ---------- Botão ( Deletar ) ----------
                
                self.btn_deletar = QtWidgets.QPushButton("X")
                self.btn_deletar.setObjectName("btn_deletar")
                self.btn_deletar.setMaximumWidth(30)
                self.btn_deletar.setMaximumHeight(30)
                self.btn_deletar.clicked.connect(lambda checked = False, id_lista=id_lista: self.deletar_lista(id_lista))
                self.layout_metas.addWidget(self.btn_deletar)
               
            
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao buscar as metas: {e}")
            return
    
    # ---------- Deletar Lista ----------
    
    def deletar_lista(self, id_lista):
        try:
            
            cursor.execute(f"DROP TABLE IF EXISTS lista_{id_lista};")
            cursor.execute("DELETE FROM metas WHERE id = ?;", (id_lista,))
            conexao.commit()
            
            self.mostrar_lista_metas()
            
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao deletar a lista: {e}")
            return
    
    # ---------- Exportar -----------
    
    def exportar(self, id_lista):
        
        try:
            
            cursor.execute("SELECT titulo, prazo FROM metas WHERE id = ?", (id_lista,))
            titulo, prazo = cursor.fetchone()
            
            cursor.execute(f"SELECT meta, estado FROM lista_{int(id_lista)}")
            metas = [{"meta": meta, "estado": estado} for meta, estado in cursor.fetchall()]
            
            dados = {
                "titulo": titulo,
                "prazo": prazo,
                "metas": metas,
            }
            
            caminho, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Salvar lista",
                "lista.json",
                "Arquivos JSON (*.json)",
            )
            
            if not caminho:
                return
            
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=4)
            
            
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro para exportar a lista: {e}")
            return
        
# ---------- Tela Objetivos ----------

class tela_metas(QtWidgets.QWidget):
    tema_alterado = QtCore.Signal(str)
    
    def __init__(self, stack):
        super().__init__()
        
        self.stack = stack
        self.id_lista_atual = None
        
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        
        # ---------- Título ----------
        
        self.titulo = QtWidgets.QLabel("Metas e Objetivos !!")
        self.titulo.setObjectName("titulo_metas")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.titulo, 0, 1, 1, 2)
        
        # --------- Temas ----------
                
        self.temas = QtWidgets.QComboBox()
        self.temas.addItems(["dark", "light"])
        self.temas.setObjectName("temas")
        self.temas.currentTextChanged.connect(self.tema_alterado.emit)   
        self.layout.addWidget(self.temas, 0, 0)
        
        # --------- Botão ( Voltar ) ----------
        
        self.btn_voltar = QtWidgets.QPushButton("Voltar")
        self.btn_voltar.setObjectName("btn_voltar")
        self.btn_voltar.clicked.connect(self.voltar_para_lista)
        self.layout.addWidget(self.btn_voltar, 0, 3)
        
        # --------- Scroll das metas ------------
        
        self.scroll_metas = QtWidgets.QScrollArea()
        self.scroll_metas.setObjectName("scroll_metas")
        self.scroll_metas.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_metas.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_metas.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scroll_metas.setMinimumHeight(300)
        self.scroll_metas.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_metas, 1, 0, 4, 4)
        
        # --------- Frame ( Lista de metas ) ----------
        
        self.frame_lista_meta = QtWidgets.QFrame()
        self.frame_lista_meta.setObjectName("frame_lista_meta")
        self.scroll_metas.setWidget(self.frame_lista_meta)
        
        self.layout_meta = QtWidgets.QVBoxLayout(self.frame_lista_meta, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self.layout_meta.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        
        # ---------- Chamar a função ----------
        
        self.mostrar_metas()
        
        
        # --------- Botão Criar nova meta ---------
        
        self.btn_nova_meta = QtWidgets.QPushButton("Criar nova meta !")
        self.btn_nova_meta.setObjectName("btn_nova_meta")
        self.btn_nova_meta.clicked.connect(self.criar_meta)
        self.btn_nova_meta.setMinimumHeight(40)
        self.btn_nova_meta.setMaximumHeight(50)
        self.btn_nova_meta.setMinimumWidth(200)
        self.layout.addWidget(self.btn_nova_meta, 5, 1, 1, 2)
        
    # ---------- Funções ----------
        
    # --------- Pegar o id da lista ----------
        
    def pegar_id_lista(self, id_lista):
        self.id_lista_atual = id_lista
        self.mostrar_metas()
        
    # --------- Trocar Tela ----------
        
    def voltar_para_lista(self):
        self.stack.setCurrentIndex(1)
        
    # --------- Apagar layout --------
        
    def limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.limpar_layout(item.layout())
                
    # ---------- Completar metas -----------  
                            
    def completar_meta(self, id, estado):
        novo_estado = "completo" if estado == "pendente" else "pendente"
        
        try:    
            
            cursor.execute(f"UPDATE lista_{int(self.id_lista_atual)} SET estado = ? WHERE id = ?", (novo_estado, id,))
            conexao.commit()
                   
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao buscar as metas: {e}")
            return        
        
        self.mostrar_metas()
                
    # ---------- Mostras todas as metas ----------
        
    def mostrar_metas(self):
            
        if self.id_lista_atual is None:
            return
                  
        self.limpar_layout(self.layout_meta)
        
        try:     
            cursor.execute(f"SELECT id, meta, estado FROM lista_{int(self.id_lista_atual)};")
            metas = cursor.fetchall()
            
            for id, nome_meta, estado in metas:
            
            # --------- Frame ( Objetivos ) ----------
                    
                self.frame_Obje = QtWidgets.QFrame()
                self.frame_Obje.setObjectName("frame_Obje")
                self.frame_Obje.setMinimumHeight(40)
                self.frame_Obje.setMaximumWidth(800)
                self.frame_Obje.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding,
                    QtWidgets.QSizePolicy.Policy.Minimum,
                )
                self.layout_meta.addWidget(self.frame_Obje)
                
                self.layout_Obje = QtWidgets.QHBoxLayout(self.frame_Obje)
            
            # --------- Botão ( Verificar ) ----------
            
                if estado == "pendente":
                        
                    self.btn_verificar = QtWidgets.QPushButton("O")
                    self.btn_verificar.setObjectName("btn_verificar_pendente")
                    self.btn_verificar.setMaximumWidth(30)
                    self.btn_verificar.setMaximumHeight(30)
                    self.btn_verificar.clicked.connect(lambda checked = False, id = id, estado = estado: self.completar_meta(id, estado) )
                    
                    self.layout_Obje.addWidget(self.btn_verificar)
                    
                elif estado == "completo":
                    
                    self.btn_verificar = QtWidgets.QPushButton("✔")
                    self.btn_verificar.setObjectName("btn_verificar")
                    self.btn_verificar.setMaximumWidth(30)
                    self.btn_verificar.setMaximumHeight(30)
                    self.btn_verificar.clicked.connect(lambda checked = False, id = id, estado = estado: self.completar_meta(id, estado) )

                    self.layout_Obje.addWidget(self.btn_verificar)
                else:
                    
                    self.btn_verificar = QtWidgets.QPushButton("E")
                    self.btn_verificar.setObjectName("btn_verificar_erro")
                    self.btn_verificar.setMaximumWidth(30)
                    self.btn_verificar.setMaximumHeight(30)
                    self.btn_verificar.clicked.connect(lambda checked = False, id = id, estado = estado: self.completar_meta(id, estado) )

                    self.layout_Obje.addWidget(self.btn_verificar)    
                                   
            # --------- Objetivo ----------
               
                self.objetivo = QtWidgets.QLabel("\u200b".join(nome_meta))
                self.objetivo.setObjectName("objetivo")
                self.objetivo.setMaximumWidth(600)
                self.objetivo.setMinimumHeight(50)
                self.objetivo.setWordWrap(True)
                self.objetivo.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction) 
                self.objetivo.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                self.layout_Obje.addWidget(self.objetivo, stretch= 1)
                
            # --------- Botão ( Editar ) ----------
            
                self.btn_editar = QtWidgets.QPushButton("E")
                self.btn_editar.setObjectName("btn_editar")
                self.btn_editar.setMaximumHeight(30)
                self.btn_editar.setMaximumWidth(30)
                self.btn_editar.clicked.connect(lambda checked = False, id =id, meta_atual = nome_meta: self.editar_meta(id, meta_atual))
                self.layout_Obje.addWidget(self.btn_editar)
                
            # --------- Botão ( Deletar ) ----------
                    
                self.btn_deletar = QtWidgets.QPushButton("X")
                self.btn_deletar.setObjectName("btn_deletar_meta")
                self.btn_deletar.setMaximumWidth(30)
                self.btn_deletar.setMaximumHeight(30)
                self.btn_deletar.clicked.connect(lambda checked = False, id = id: self.apagar_meta(id))
                self.layout_Obje.addWidget(self.btn_deletar)
                
            # --------- Chamada de função ----------
            
                self.mostrar_prazo()
                    
                
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao buscar as metas: {e}")
            return
        
    # --------- Deletar Meta ----------
    
    def apagar_meta(self, id_meta):
        
        try:
            cursor.execute(f"DELETE FROM lista_{int(self.id_lista_atual)} WHERE id = ?;", (id_meta,))
            conexao.commit()
            
            self.mostrar_metas()
        
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao buscar as metas: {e}")
            return               
    
    # --------- Criar Meta -----------
    
    def criar_meta(self):
        
        meta_nova, confirmacao = QtWidgets.QInputDialog.getText(self, "Nova meta", "Nome da meta: ")
        
        if not confirmacao:
            return
        
        if confirmacao and meta_nova.strip() == "":
            QtWidgets.QMessageBox.critical(self,"Error", "Coloque um valor novo para a meta")
            return

        try:
            
            cursor.execute(f"INSERT INTO lista_{int(self.id_lista_atual)} (meta, id_lista) VALUES (?, ?)", (meta_nova, int(self.id_lista_atual)))
            conexao.commit()
            
            self.mostrar_metas()
            
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao criar meta: {e}")
            return  
           
    # -------- Editar Meta -----------
    
    def editar_meta(self, id_meta, meta_atual):
        
        nova_meta, confirmacao = QtWidgets.QInputDialog.getText(self, "Editar meta", "Coloque como a meta vai ficar !", text=meta_atual)

        if not confirmacao:
            return
        
        if confirmacao and  nova_meta.strip() is None:
            return
        
        try:
            
            cursor.execute(f"UPDATE lista_{int(self.id_lista_atual)} SET meta = ? WHERE id = ? ;", (nova_meta, id_meta))
            conexao.commit()
            
            self.mostrar_metas()
                        
        except sqlite3.Error as e :
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao editar : {e}")
            return  
                          
    # -------- Mostrar Prazo ---------
    
    def mostrar_prazo(self):
        
        try:
            
            cursor.execute(f"SELECT prazo FROM metas WHERE id = {int(self.id_lista_atual)} ;")
            
            prazo = datetime.strptime(cursor.fetchone()[0], "%Y-%m-%d")
            prazo_formatado = prazo.strftime("%d/%m/%Y")
            
            prazo_comparação = prazo.date()
            data_atual = date.today()
            dias_restantes = (prazo_comparação - data_atual).days
            
            if dias_restantes > 0:
                 
            # --------- Prazo -------------
                        
                self.prazo_final = QtWidgets.QLabel(f"Você ainda tem {dias_restantes} dias \n prazo final: " + prazo_formatado)
                self.prazo_final.setObjectName("prazo_final")
                self.prazo_final.setMinimumHeight(50)
                self.prazo_final.setWordWrap(True)
                self.prazo_final.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                
                self.layout.addWidget(self.prazo_final, 5, 3)

            elif dias_restantes == 0:
                
            # --------- Prazo -------------
                                        
                self.prazo_final = QtWidgets.QLabel(f"Você só tem até hoje, vamos nessa !! \n prazo final: " + prazo_formatado)
                self.prazo_final.setObjectName("prazo_final")
                self.prazo_final.setMinimumHeight(50)
                self.prazo_final.setWordWrap(True)
                self.prazo_final.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                
                self.layout.addWidget(self.prazo_final, 5, 3)
                
            elif dias_restantes < 0:
                
            # --------- Prazo -------------
                                        
                self.prazo_final = QtWidgets.QLabel(f"Você perdeu por {abs(dias_restantes)} dias \n prazo final: " + prazo_formatado)
                self.prazo_final.setObjectName("prazo_final")
                self.prazo_final.setMinimumHeight(50)
                self.prazo_final.setWordWrap(True)
                self.prazo_final.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                
                self.layout.addWidget(self.prazo_final, 5, 3)
            
            else:
                
            # --------- Prazo -------------
                                        
                self.prazo_final = QtWidgets.QLabel(f"Erro")
                self.prazo_final.setObjectName("prazo_final")
                self.prazo_final.setMinimumHeight(50)
                self.prazo_final.setWordWrap(True)
                self.prazo_final.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                
                self.layout.addWidget(self.prazo_final, 5, 3)

            # --------- Aviso --------
                
                QtWidgets.QMessageBox.critical(self, "Erro", f"Erro em mostrar o prazo")
    
            
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro em mostrar o prazo: {e}")
            return
                                             
# ---------- Tela Criação de listas ---------- 

class tela_criacao(QtWidgets.QWidget):
    tema_alterado = QtCore.Signal(str)
    
    def __init__(self, stack):
        super().__init__()
        
        self.stack = stack
        
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        
        # ---------- Título ----------
        
        self.titulo = QtWidgets.QLabel("Criação de Lista !!")
        self.titulo.setObjectName("titulo_criacao")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.titulo, 0, 1, 1, 2)
        
        #--------- Botão ( Voltar ) ----------
        
        self.btn_voltar = QtWidgets.QPushButton("Voltar")
        self.btn_voltar.setObjectName("btn_voltar")
        self.btn_voltar.clicked.connect(self.voltar_para_inicial)
        self.layout.addWidget(self.btn_voltar, 0, 3)
        
        # --------- Temas ----------
        
        self.temas = QtWidgets.QComboBox()
        self.temas.addItems(["dark", "light"])
        self.temas.setObjectName("temas")
        self.temas.currentTextChanged.connect(self.tema_alterado.emit)
        self.layout.addWidget(self.temas, 0, 0)
        
        # --------- Frame ( Criação de Lista ) ----------
        
        self.frame_criacao = QtWidgets.QFrame()
        self.frame_criacao.setObjectName("frame_criacao")
        self.layout.addWidget(self.frame_criacao, 1, 0, 4, 4)
        
        self.layout_criacao = QtWidgets.QFormLayout(self.frame_criacao)
        
        # ---------- Campo ( titulo da Lista ) ----------
            
        self.input_titulo_lista = QtWidgets.QLineEdit()
        self.input_titulo_lista.setObjectName("input_titulo_lista")
        self.input_titulo_lista.setMinimumHeight(30)
        self.input_titulo_lista.setPlaceholderText("Digite o título da lista")
        self.layout_criacao.addRow("Título da Lista:", self.input_titulo_lista)
        
         # ---------- Campo ( Metas da Lista ) ----------
        
        self.input_meta = QtWidgets.QTextEdit()
        self.input_meta.setObjectName("input_meta")
        self.input_meta.setPlaceholderText("Digite as metas da lista, separadas por vírgula")
        self.layout_criacao.addRow("Metas da Lista:", self.input_meta)
        
        # ---------- Campo ( Prazo ) ----------
            
        self.input_prazo = QtWidgets.QDateEdit()
        self.input_prazo.setObjectName("input_prazo")
        self.input_prazo.setCalendarPopup(True)
        self.input_prazo.setDate(QtCore.QDate.currentDate())
        self.input_prazo.setMinimumHeight(30)
        self.layout_criacao.addRow("Prazo:", self.input_prazo)

        # --------- Botão ( Enviar Lista ) ----------
        
        self.btn_enviar = QtWidgets.QPushButton("Enviar Lista")
        self.btn_enviar.setObjectName("btn_enviar")
        self.btn_enviar.clicked.connect(self.criar_metas)
        self.btn_enviar.setMinimumHeight(35)
        self.layout.addWidget(self.btn_enviar, 5, 1)
        
        # --------- Botão ( Limpar Campos ) ----------
        
        self.btn_limpar = QtWidgets.QPushButton("Limpar Campos")
        self.btn_limpar.setObjectName("btn_limpar")
        self.btn_limpar.setMinimumHeight(35)
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.layout.addWidget(self.btn_limpar, 5, 2)

        # --------- Funções ----------
        # --------- Trocar Tela ----------
        
    def voltar_para_inicial(self):
        self.stack.setCurrentIndex(0) 
        
    # ---------- Funções de Limpeza ----------
        
    def limpar_campos(self):
        self.input_titulo_lista.clear()
        self.input_meta.clear()
        self.input_prazo.setDate(QtCore.QDate.currentDate())
        
    # ----------- Validar Campos ----------
        
    def validar_campos(self):
        
        if not self.input_titulo_lista.text().strip():
            QtWidgets.QMessageBox.warning(self, "Erro", "O Título da Lista não pode estar vazio.")
            self.input_titulo_lista.setFocus()
            return False
        
        if len(self.input_titulo_lista.text().strip()) > 20:
            QtWidgets.QMessageBox.warning(self, "Erro", "O Título da Lista não pode ter mais de 20 caracteres.")
            self.input_titulo_lista.setFocus()
            return False
            
        return True
    
    # ----------- Criar Metas ----------
    
    def criar_metas(self):
        
        if not self.validar_campos():
            return
        
        titulo = self.input_titulo_lista.text()
        metas = self.input_meta.toPlainText().split(",")
        prazo = self.input_prazo.date().toString("yyyy-MM-dd")
        
        try:
            cursor.execute("""
                INSERT INTO metas (titulo, prazo) VALUES (?, ?);          
            """, (titulo, prazo))
            
            cursor.execute("SELECT id FROM metas WHERE titulo = ?", (titulo,))
            id_lista = cursor.fetchone()[0]
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS lista_{id_lista} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meta TEXT NOT NULL,
                    id_lista INTEGER,
                    estado TEXT DEFAULT 'pendente',
                    FOREIGN KEY (id_lista) REFERENCES metas(id)
                );
            """)
            
            for meta in metas:
                cursor.execute(f"""
                    INSERT INTO lista_{id_lista} (meta, id_lista) VALUES (?, ?);
                """, (meta, id_lista))
                
            
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Erro", f"Erro ao criar a lista: {e}")
            print("Erro ao criar a lista:", e)
            return
        
        conexao.commit()

        self.limpar_campos()
        self.stack.setCurrentIndex(0)
         
# ---------- Tela Principal ----------

class tela_principal(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.pasta_temas = self.caminho_recurso("styles")

        self.setWindowTitle("Lista de Objetivos")
        self.resize(600, 500)
        
            
        self.stack = QtWidgets.QStackedWidget()
        self.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.stack)
        
        self.tela_inicial = tela_inicial(self.stack)
        self.tela_lista = tela_lista(self.stack)
        self.tela_metas = tela_metas(self.stack)
        self.tela_criacao = tela_criacao(self.stack)
        
        self.stack.addWidget(self.tela_inicial)
        self.stack.addWidget(self.tela_lista)
        self.stack.addWidget(self.tela_metas)
        self.stack.addWidget(self.tela_criacao)
        
        self.stack.setCurrentIndex(0)
        
        for tela in (self.tela_inicial, self.tela_lista, self.tela_metas, self.tela_criacao):
            tela.tema_alterado.connect(self.trocar_tema)

        self.trocar_tema("dark")
        
        self.tela_lista.lista_atual.connect(self.tela_metas.pegar_id_lista)
        
    # ---------- Funções ----------
    
    # --------- Caminho dos temas ---------
    
    def caminho_recurso(self, relativo):
        
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, relativo)
    
    # --------- Trocar temas ---------
        
    def trocar_tema(self, tema):
        caminho_qss = os.path.join(self.pasta_temas, f"{tema}.qss")

        if not os.path.exists(caminho_qss):
            print(f"Arquivo de estilo não encontrado: {caminho_qss}")
            return

        with open(caminho_qss, "r", encoding="utf-8") as arquivo:
            self.setStyleSheet(arquivo.read())  

        for tela in (self.tela_inicial, self.tela_lista, self.tela_metas, self.tela_criacao):
            combo = tela.temas
            combo.blockSignals(True)
            combo.setCurrentText(tema)
            combo.blockSignals(False)
       
# ---------- Main ----------
           
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ListaDeMetas")
    janela = tela_principal()
    janela.show()
    sys.exit(app.exec())