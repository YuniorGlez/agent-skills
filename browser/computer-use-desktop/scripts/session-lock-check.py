#!/usr/bin/env python3
"""¿Está bloqueada la pantalla y hay alguien delante del Mac?

Sin dependencias: CoreGraphics por ctypes. Imprime LOCKED o UNLOCKED, los segundos de inactividad
de teclado/ratón y quién tiene el foco. Salida 0 siempre (es informativo).

Con LOCKED no hay árbol de accesibilidad utilizable: cualquier herramienta de computer use fallará.
"""
import ctypes
import subprocess


def session_state():
    cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    cg.CGSessionCopyCurrentDictionary.restype = ctypes.c_void_p
    cf.CFCopyDescription.argtypes = [ctypes.c_void_p]
    cf.CFCopyDescription.restype = ctypes.c_void_p
    cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
    d = cg.CGSessionCopyCurrentDictionary()
    if not d:
        return None
    buf = ctypes.create_string_buffer(4000)
    cf.CFStringGetCString(cf.CFCopyDescription(d), buf, 4000, 0x08000100)
    return buf.value.decode(errors="replace")


def idle_seconds():
    try:
        out = subprocess.run(["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            if "HIDIdleTime" in line:
                return int(line.split()[-1]) / 1e9
    except Exception:
        pass
    return None


def front_owner():
    try:
        out = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True, timeout=10).stdout
        if "loginwindow" in out:
            return "loginwindow"
        return out.strip().splitlines()[0] if out.strip() else "?"
    except Exception:
        return "?"


if __name__ == "__main__":
    state = session_state()
    if state is None:
        print("NO-GUI-SESSION")
        raise SystemExit(0)
    locked = "CGSSessionScreenIsLocked = 1" in state
    idle = idle_seconds()
    print("LOCKED" if locked else "UNLOCKED")
    print(f"idle: {idle:.0f} s" if idle is not None else "idle: ?")
    print(f"frente: {front_owner()}")
    if locked:
        print("Con la pantalla bloqueada no hay árbol de accesibilidad: ninguna herramienta de computer use funciona.")
