#!/usr/bin/env python3
"""Activa la accesibilidad manual (AXManualAccessibility) en un pid, como hace VoiceOver.

Uso: python3 ax_enable.py <pid>
"""
import ctypes
import sys

AS = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
CF = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')

AS.AXUIElementCreateApplication.argtypes = [ctypes.c_int]
AS.AXUIElementCreateApplication.restype = ctypes.c_void_p
AS.AXUIElementSetAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
AS.AXUIElementSetAttributeValue.restype = ctypes.c_int
AS.AXUIElementCopyAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
AS.AXUIElementCopyAttributeValue.restype = ctypes.c_int
CF.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
CF.CFStringCreateWithCString.restype = ctypes.c_void_p

TRUE = ctypes.c_void_p.in_dll(CF, "kCFBooleanTrue")
FALSE = ctypes.c_void_p.in_dll(CF, "kCFBooleanFalse")


def cfstr(s):
    return CF.CFStringCreateWithCString(None, s.encode(), 0x08000100)


pid = int(sys.argv[1])
app = AS.AXUIElementCreateApplication(pid)
print("app element:", hex(app) if app else None)

for attr in ("AXManualAccessibility", "AXEnhancedUserInterface"):
    err = AS.AXUIElementSetAttributeValue(app, cfstr(attr), TRUE)
    val = ctypes.c_void_p()
    err2 = AS.AXUIElementCopyAttributeValue(app, cfstr(attr), ctypes.byref(val))
    print(f"  {attr}: set={err} read={err2} value={'true' if val.value == TRUE.value else 'false/other'}")
