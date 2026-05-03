"""Cython-модуль для критичных к производительности операций.

Компиляция:
    python setup.py build_ext --inplace
"""

cpdef unsigned int fast_checksum_cython(bytes data):
    """Быстрая контрольная сумма (Cython-версия)."""
    cdef unsigned int result = 0
    cdef Py_ssize_t i
    cdef unsigned char val
    for i in range(len(data)):
        val = data[i]
        result = (result * 31 + val) & 0xFFFFFFFF
    return result

cpdef unsigned int fast_hash_string_cython(str s):
    """Быстрый хеш строки (Cython-версия)."""
    cdef unsigned int result = 0
    cdef Py_ssize_t i
    for i in range(len(s)):
        result = (result * 31 + <unsigned int>ord(s[i])) & 0xFFFFFFFF
    return result
