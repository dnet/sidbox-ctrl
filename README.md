SIDbox controller consists of several building blocks, which form a low to high-level API to the SIDbox project at the Hungarian Autonomous Center for Knowledge (H.A.C.K.).

Low-level C API
=============

The low-level API provides several primitives in sid.c

 - to initialize the parallel port (sid_init),
 - to reset the SID chip (sid_reset), and
 - to write a byte in a selected SID register (sid_write).

This interface is pretty *nix-specific at the moment (we only tested it on Linux, although it should work on BSDs, too) and uses LPT1 by default (you can change it by redefining PDATA and PSTAT in sid.c). Because of the direct I/O calls, it needs root privileges.

The low-level API's functionality can be tested using the test.c program, which plays a single note using SID voice 1.

Standard I/O and TCP interface
==============================

A simple program called cat.c translates two byte commands into SID writes, which comes with two advantages:

 - the high-level controller doesn't need root privileges (the ./cat binary can be made SUID root), and
 - any programming language which can write to the standard output can be used to control the SIDbox.

The TCP interface makes the whole construct even more extensible by adding a netcat TCP listener to cat's standard input, so the SIDbox can be controlled from any other networked machine (even on the other side of the Internet).

High-level Python API
=====================

The high-level API makes controlling the SIDbox a pretty easy task. By importing and instantiating the SID class from sid.py, many features of the SIDbox are easily accessible through managed interfaces, and it's also trivial to access the remaining ones through the rawrite() method. A simple piano application (piano.py), developed for demonstration and testing purposes provides a working example on the usage of this interface.
