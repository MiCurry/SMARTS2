import os

class pgi_check:
    test_name = "PGI Compiler Check"
    test_description = "Check to see if there is a PGI compiler is on the machine and able to be" \
                       " found by SMARTs"
    ncpus = 1

    def run(self, env, result, src_dir, test_dir, hpc=None, *args, **kwargs):

        # Load PGI Compilers
        pgi_modsets = env.list_modsets(name="PGI")
        if len(pgi_modsets) == 0:
            result.result = "FAILED"
            result.msg = "Could not load any PGI Modsets!"
            return -1

        for versions in pgi_modsets:
            # For each compiler, test to see if we can make, and compile simple
            # C and Fortran programs
            modset = env.load_modset(versions)
            if not modset:
                result.result = "FAILED"
                result.msg = "Failed to load "+versions
                return -1

            simple_c_prog = "int main(void) { return 0; }"
            simple_fortran_prog = "end"

            c_prog_file = open('./simple_c_prog.c', 'w')
            c_prog_file.write(simple_c_prog)
            c_prog_file.close()

            # Check to see if the c program source file was written
            if not os.path.isfile('./simple_c_prog.c'):
                result.result = "FAILED"
                result.msg = "Unable to create ./simple_c_prog.c"
                return -1

            fortran_prog_file = open('./simple_fortran_prog.f90', 'w')
            fortran_prog_file.write(simple_fortran_prog)
            fortran_prog_file.close()

            # Check to see if the fortran source file was written
            if not os.path.isfile('./simple_fortran_prog.f90'):
                result.result = "FAILED"
                result.msg = "Unable to create ./simple_fortran_prog.f90"
                return -1

            # Compiler c program and check to see if it compiles correctly 
            if os.system('pgcc -o c_prog simple_c_prog.c') != 0:
                result.result = "FAILED"
                result.msg = "Failed to copmile simple_c_prog.c with gcc/"+version
                return -1
            
            # Compile Fortran program and check to see if it compiles correctly
            if os.system('pgfortran -o f_prog simple_fortran_prog.f90') != 0:
                result.result = "FAILED"
                result.msg = "Failed to copmile simple_c_prog.c with gcc/"+version
                return -1

        result.result = "PASSED"
        result.msg = "PGI Check Completed! - All programs compiled"
        return 0
