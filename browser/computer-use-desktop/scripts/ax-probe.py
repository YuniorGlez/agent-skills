#!/usr/bin/env python3
"""Sonda directa al árbol de accesibilidad de un proceso (macOS, sin dependencias).

Uso: python3 ax-probe.py <pid>

Sirve para distinguir tres causas que se ven igual desde fuera:
  - AXIsProcessTrusted() False   -> el proceso que lanza no tiene accesibilidad
  - True pero AXWindows vacío    -> la app no expone ventanas (o sesión bloqueada)
  - True y N ventanas            -> el árbol existe: el fallo es de la herramienta, no del sistema

`osascript -e '… count windows'` NO sirve para esto: devuelve 0 en silencio cuando faltan permisos.
"""
import ctypes
import sys

AS = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
CF = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")

AS.AXIsProcessTrusted.restype = ctypes.c_bool
AS.AXUIElementCreateApplication.argtypes = [ctypes.c_int]
AS.AXUIElementCreateApplication.restype = ctypes.c_void_p
AS.AXUIElementCopyAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
AS.AXUIElementCopyAttributeValue.restype = ctypes.c_int
CF.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
CF.CFStringCreateWithCString.restype = ctypes.c_void_p
CF.CFArrayGetCount.argtypes = [ctypes.c_void_p]
CF.CFArrayGetCount.restype = ctypes.c_long
CF.CFGetTypeID.argtypes = [ctypes.c_void_p]
CF.CFGetTypeID.restype = ctypes.c_ulong
CF.CFArrayGetTypeID.restype = ctypes.c_ulong
CF.CFStringGetTypeID.restype = ctypes.c_ulong
CF.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
CF.CFStringGetCString.restype = ctypes.c_bool


def cfstr(text):
    return CF.CFStringCreateWithCString(None, text.encode(), 0x08000100)


def describe(value):
    if not value:
        return "none"
    kind = CF.CFGetTypeID(value)
    if kind == CF.CFArrayGetTypeID():
        return f"array count={CF.CFArrayGetCount(value)}"
    if kind == CF.CFStringGetTypeID():
        buf = ctypes.create_string_buffer(512)
        CF.CFStringGetCString(value, buf, 512, 0x08000100)
        return f"string={buf.value.decode(errors='replace')!r}"
    return f"type={kind}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    pid = int(sys.argv[1])
    print("AXIsProcessTrusted():", AS.AXIsProcessTrusted())
    app = AS.AXUIElementCreateApplication(pid)
    print("app element:", hex(app) if app else None)
    for attr in ("AXWindows", "AXTitle", "AXRole"):
        value = ctypes.c_void_p()
        err = AS.AXUIElementCopyAttributeValue(app, cfstr(attr), ctypes.byref(value))
        print(f"  {attr}: err={err} {describe(value.value)}")
