import os
import sys
import time
import socket
import webbrowser
import subprocess
import traceback
from pathlib import Path
import ctypes
from ctypes import wintypes


BASE_DIR = Path(__file__).resolve().parent
APP_PATH = BASE_DIR / "app.py"
ICON_PATH = BASE_DIR / "pizza.ico"
LOG_PATH = BASE_DIR / "tray_pdv_erro.log"
URL_PDV = "http://127.0.0.1:5000"

server_process = None


def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"\n[{time.strftime('%d/%m/%Y %H:%M:%S')}] {msg}")
    except Exception:
        pass


def salvar_erro(erro):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
            arquivo.write("\n\n================ ERRO ================\n")
            arquivo.write(time.strftime("%d/%m/%Y %H:%M:%S"))
            arquivo.write("\n")
            arquivo.write(str(erro))
            arquivo.write("\n")
            arquivo.write(traceback.format_exc())
            arquivo.write("\n======================================\n")
    except Exception:
        pass


def excecao_global(tipo, valor, tb):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
            arquivo.write("\n\n================ ERRO GLOBAL ================\n")
            arquivo.write(time.strftime("%d/%m/%Y %H:%M:%S"))
            arquivo.write("\n")
            arquivo.write("".join(traceback.format_exception(tipo, valor, tb)))
            arquivo.write("\n=============================================\n")
    except Exception:
        pass


sys.excepthook = excecao_global

log("tray_pdv.py carregou o arquivo.")


try:
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32
    log("DLLs do Windows carregadas.")
except Exception as erro:
    salvar_erro(erro)
    raise


LRESULT = getattr(wintypes, "LRESULT", ctypes.c_longlong)
ATOM = getattr(wintypes, "ATOM", wintypes.WORD)
HICON = getattr(wintypes, "HICON", wintypes.HANDLE)
HCURSOR = getattr(wintypes, "HCURSOR", wintypes.HANDLE)
HBRUSH = getattr(wintypes, "HBRUSH", wintypes.HANDLE)
HMENU = getattr(wintypes, "HMENU", wintypes.HANDLE)
HINSTANCE = getattr(wintypes, "HINSTANCE", wintypes.HANDLE)
LPVOID = getattr(wintypes, "LPVOID", ctypes.c_void_p)
LPCWSTR = getattr(wintypes, "LPCWSTR", ctypes.c_wchar_p)


WM_USER = 0x0400
WM_TRAYICON = WM_USER + 20
WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203

NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

IDI_APPLICATION = 32512
IMAGE_ICON = 1
LR_DEFAULTSIZE = 0x00000040
LR_SHARED = 0x00008000
LR_LOADFROMFILE = 0x00000010

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
TPM_RIGHTBUTTON = 0x0002
TPM_BOTTOMALIGN = 0x0020

SW_HIDE = 0

MENU_ABRIR = 1001
MENU_SAIR = 1002


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", HICON),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
)


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR),
    ]


def configurar_funcoes_windows():
    log("Configurando funções do Windows.")

    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
    user32.RegisterClassW.restype = ATOM

    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        LPCWSTR,
        LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        HMENU,
        HINSTANCE,
        LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND

    user32.DefWindowProcW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.DefWindowProcW.restype = LRESULT

    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL

    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.PostQuitMessage.restype = None

    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.LoadImageW.argtypes = [
        HINSTANCE,
        LPCWSTR,
        wintypes.UINT,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.LoadImageW.restype = wintypes.HANDLE

    shell32.Shell_NotifyIconW.argtypes = [
        wintypes.DWORD,
        ctypes.POINTER(NOTIFYICONDATA),
    ]
    shell32.Shell_NotifyIconW.restype = wintypes.BOOL

    log("Funções do Windows configuradas.")


def MAKEINTRESOURCE(i):
    return ctypes.cast(ctypes.c_void_p(i), LPCWSTR)


def LOWORD(value):
    return int(value) & 0xFFFF


def porta_esta_aberta(host="127.0.0.1", port=5000):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def caminho_python_console():
    exe_atual = Path(sys.executable)

    log(f"Python atual: {exe_atual}")

    if exe_atual.name.lower() == "pythonw.exe":
        python_exe = exe_atual.with_name("python.exe")
    else:
        python_exe = exe_atual

    log(f"Python usado para iniciar Flask: {python_exe}")

    return str(python_exe)


def iniciar_servidor():
    global server_process

    log("Verificando servidor na porta 5000.")

    if porta_esta_aberta():
        log("Porta 5000 já está aberta. Servidor parece estar rodando.")
        return

    if not APP_PATH.exists():
        raise FileNotFoundError(f"app.py não encontrado em: {APP_PATH}")

    python_exe = caminho_python_console()

    creationflags = 0

    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    log("Iniciando Flask escondido.")

    server_process = subprocess.Popen(
        [python_exe, str(APP_PATH)],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags
    )

    log(f"Servidor Flask iniciado. PID: {server_process.pid}")


def aguardar_servidor(timeout=25):
    log("Aguardando servidor responder.")

    inicio = time.time()

    while time.time() - inicio < timeout:
        if porta_esta_aberta():
            log("Servidor respondeu na porta 5000.")
            return True

        time.sleep(0.5)

    log("Servidor não respondeu dentro do tempo limite.")
    return False


def abrir_pdv():
    try:
        log("Abrir PDV solicitado.")

        if not porta_esta_aberta():
            iniciar_servidor()
            aguardar_servidor()

        webbrowser.open(URL_PDV)
        log("PDV aberto no navegador.")
    except Exception as erro:
        salvar_erro(erro)


def parar_servidor():
    global server_process

    try:
        log("Parando servidor.")

        if server_process and server_process.poll() is None:
            server_process.terminate()

            try:
                server_process.wait(timeout=5)
            except Exception:
                server_process.kill()

        server_process = None
        log("Servidor parado.")
    except Exception as erro:
        salvar_erro(erro)


class TrayApp:
    def __init__(self):
        self.hwnd = None
        self.hicon = None
        self.nid = None
        self.wndproc = WNDPROC(self.window_proc)

    def criar_janela_oculta(self):
        log("Criando janela oculta do tray.")

        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "PDV_PIZZARIA_TRAY_WINDOW"

        wndclass = WNDCLASS()
        wndclass.style = 0
        wndclass.lpfnWndProc = self.wndproc
        wndclass.cbClsExtra = 0
        wndclass.cbWndExtra = 0
        wndclass.hInstance = hinstance
        wndclass.hIcon = None
        wndclass.hCursor = None
        wndclass.hbrBackground = None
        wndclass.lpszMenuName = None
        wndclass.lpszClassName = class_name

        atom = user32.RegisterClassW(ctypes.byref(wndclass))

        if not atom:
            erro = ctypes.GetLastError()
            if erro != 1410:
                raise ctypes.WinError(erro)

        self.hwnd = user32.CreateWindowExW(
            0,
            class_name,
            "PDV Pizzaria Tray",
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            hinstance,
            None
        )

        if not self.hwnd:
            raise ctypes.WinError(ctypes.GetLastError())

        user32.ShowWindow(self.hwnd, SW_HIDE)

        log("Janela oculta criada.")

    def carregar_icone_personalizado(self):
        log(f"Tentando carregar ícone personalizado: {ICON_PATH}")

        if ICON_PATH.exists():
            hicon = user32.LoadImageW(
                None,
                str(ICON_PATH),
                IMAGE_ICON,
                0,
                0,
                LR_LOADFROMFILE | LR_DEFAULTSIZE
            )

            if hicon:
                log("Ícone personalizado carregado com sucesso.")
                return hicon

            log("Falha ao carregar pizza.ico. Vai usar ícone padrão do Windows.")

        else:
            log("Arquivo pizza.ico não encontrado. Vai usar ícone padrão do Windows.")

        hicon = user32.LoadImageW(
            None,
            MAKEINTRESOURCE(IDI_APPLICATION),
            IMAGE_ICON,
            0,
            0,
            LR_DEFAULTSIZE | LR_SHARED
        )

        return hicon

    def adicionar_icone(self):
        log("Adicionando ícone na bandeja.")

        self.hicon = self.carregar_icone_personalizado()

        if not self.hicon:
            raise ctypes.WinError(ctypes.GetLastError())

        self.nid = NOTIFYICONDATA()
        self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATA)
        self.nid.hWnd = self.hwnd
        self.nid.uID = 1
        self.nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        self.nid.uCallbackMessage = WM_TRAYICON
        self.nid.hIcon = self.hicon
        self.nid.szTip = "PDV Pizzaria"

        ok = shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self.nid))

        if not ok:
            raise ctypes.WinError(ctypes.GetLastError())

        log("Ícone adicionado na bandeja.")

    def remover_icone(self):
        try:
            if self.nid:
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.nid))
                log("Ícone removido da bandeja.")
        except Exception as erro:
            salvar_erro(erro)

    def mostrar_menu(self):
        menu = user32.CreatePopupMenu()

        user32.AppendMenuW(menu, MF_STRING, MENU_ABRIR, "Abrir PDV")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, MENU_SAIR, "Parar servidor e sair")

        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))

        user32.SetForegroundWindow(self.hwnd)

        user32.TrackPopupMenu(
            menu,
            TPM_RIGHTBUTTON | TPM_BOTTOMALIGN,
            point.x,
            point.y,
            0,
            self.hwnd,
            None
        )

        user32.DestroyMenu(menu)

    def window_proc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_TRAYICON:
                if lparam == WM_RBUTTONUP:
                    self.mostrar_menu()
                    return 0

                if lparam == WM_LBUTTONDBLCLK:
                    abrir_pdv()
                    return 0

            if msg == WM_COMMAND:
                command_id = LOWORD(wparam)

                if command_id == MENU_ABRIR:
                    abrir_pdv()
                    return 0

                if command_id == MENU_SAIR:
                    self.sair()
                    return 0

            if msg == WM_DESTROY:
                self.remover_icone()
                user32.PostQuitMessage(0)
                return 0

        except Exception as erro:
            salvar_erro(erro)

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def sair(self):
        self.remover_icone()
        parar_servidor()
        user32.DestroyWindow(self.hwnd)

    def executar(self):
        self.criar_janela_oculta()
        self.adicionar_icone()

        log("Loop do tray iniciado.")

        msg = MSG()

        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


def main():
    log("main iniciado.")

    configurar_funcoes_windows()

    iniciar_servidor()

    if aguardar_servidor():
        webbrowser.open(URL_PDV)
        log("PDV aberto no navegador.")
    else:
        log("Servidor não respondeu. Verifique o app.py.")

    app_tray = TrayApp()
    app_tray.executar()


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        salvar_erro(erro)