import subprocess
import types
import os
import signal
import sys

class HPC:
    def __init__(self, type):
        self.type = type.upper()

    def __str__(self):
        return self.type

    def __rpr__(self):
        return self.type

    def __eq__(self, other):
        return (self.type == other)

    def init_logging(self, fname):
        """ Opening fname for logging, and set self.log to it. """
        self.log = open(fname, 'w')
        return

    def close_logging(self):
        """ Flush self.log and close it """
        self.log.flush()
        self.log.close()
        return

    def log_cmd(self, cmd):
        """ Log cmd, a list, and add '\n' to it """
        self.log.write(str(cmd)+'\n')

    def launch_job(self, cmd, name, **kwargs):
        """ Run cmd in subprocess.Popen. Cmd should be a list of arguments, without whitespace.
        This function will open a log and record all commands and output from the HPC scheduler and
        return the returncode of cmd.

        This function will only be called via the PBS.launch_job or another HPC derived class. 
        
        """
        self.init_logging('smarts-hpc.'+str(name)+'.log')
        self.log_cmd(cmd)
        self.log.flush()

        # Combine STDOUT and STDERR
        job = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Terminate the HPC blocking job if we recive SIGINT - As it appears to not stop
        # automatically
        try:
            job.wait()
        except KeyboardInterrupt as e:
            job.terminate()
            stdout = str(job.stdout.read().decode('utf-8'))
            self.log.write(stdout)
            self.log.close()
            print(e)
            sys.exit(-1)

        stdout = str(job.stdout.read().decode('utf-8'))

        self.log.write(stdout)
        self.close_logging()

        return job.returncode

class PBS(HPC):
    def launch_script(self, script, **kwargs):
        """ Submit script to the PBS job queue and block until it finishes. Upon a succesfully run
        of qsub, if the job is accepted by pbs, runs and returns, True will be returned. If the job
        is not able to be submitted then False will be returned and a log file will contain the
        qsub error messages.

        The qsub command will be called with the -Wblock=true option.

        Optional keyword arguments:
        cl_options - optional - A list of command line options to pass to the qsub command, similar
                                to args used in Python's suprocess.Popen:
                                ['-r', 'n', '-M', 'foo@bar.org']
        """
        cmd = ['qsub', '-Wblock=true']

        cl_options = kwargs.get('cl_options', None)
        if cl_options:
            if not isinstance(cl_options, list):
                raise TypeError("cl_options must be a list")

            for opts in cl_options:
                cmd.append(opts)

        if not os.path.isfile(script):
            print("ERROR: HPC Could not find this PBS job script: ", script)
            return False
        else:
            cmd.append(script)

        name = script.lstrip('./')

        if HPC.launch_job(self, cmd, name) == 0:
            return True
        else:
            return False

    def launch_job(self, executables, name, wallTime, queue, nNodes, ncpus, nMPI, **kwargs):
        """ Create a PBS job script (by deafult script.pbs) and submit it to PBS using qsub. Based
        on the agrugments described below. The job will block until execution is complete. If the
        job is able to be submitted without errors and finishes, True will be returned, else False
        will be returned.

        executables - A list of exectuables to preform for this job. For instance, source a
                      environment file, and launch the init_atmosphere core. SMARTS will create a
                      job script for PBS and place these exectuables in the order they appear.
                      Example:
                      executables = ["ulimit -s unlimited",
                                     "source ~/setup_cheyenne",
                                     "mpiexec_mpt ./init_atmosphere"]
        name - A string that contains the desired name for this job
        wallTime - The wall time in HH:MM:SS.
        queue - The desired queue.
        nNodes - The number of nodes
        ncpus - The number of CPUs to use per node
        nMPI - The number of MPI tasks per node.

        Optional Keyword Arguments:
        shell - The shell to use to launch the job script and the executables. Default is
                '#!/usr/bin/env bash'
        pbs_options - A dictionary of additional PBS options. Where the key of each item
                                 is the PBS option and the value assocaited with each key is the
                                 desired value. Options will be added to the job script in the
                                 order the appear. Default is None.

                                 For instance to set and account key:
                                    pbs_options = { 'A' : "A000001" }
        script_name - Optional name to name the job script. Default is 'script.pbs'.
        """

        shell = kwargs.get('shell', '#!/usr/bin/env bash')
        pbs_options = kwargs.get('pbs_options', None)
        script_name = kwargs.get('script_name', 'script.pbs')

        opts = [shell, '\n']

        if pbs_options:
            for key, value in pbs_options.items():
                if '-' not in key:
                    opts += ['#PBS', '-'+key, value, '\n']
                else:
                    opts += ['#PBS', key, value, '\n']

        opts += ['#PBS', '-N', name, '\n']
        opts += ['#PBS', '-j', 'oe', '\n']
        opts += ['#PBS', '-q', queue, '\n']
        opts += ['#PBS', '-l', 'walltime='+wallTime, '\n']
        opts += ['#PBS', '-l']
        opts += ['select='+str(nNodes)+':'+'ncpus='+str(ncpus)+':'+'mpiprocs='+str(nMPI),'\n']
        opts += ['\n']

        if isinstance(executables, list):
            for line in executables:
                opts += [line, '\n']
        else:
            opts += [executables, '\n']

        script = open(script_name, 'w')

        for i in range(len(opts)):
            if opts[i] == '\n':
                script.write(opts[i])
            else:
                script.write(opts[i])

            if i != len(opts) - 1:
                if opts[i] != '\n' and opts[i+1] != '\n':
                    script.write(' ')
        script.close()

        qsub_cmd = ['qsub', '-Wblock=true', script_name]

        if HPC.launch_job(self, qsub_cmd, script_name) == 0:
            return True
        else:
            return False


def init_hpc(hpcType):
    """ If hpcType is the name of a HPC class, return and instance of that class, if not return
    None. """
    if hpcType.upper() == "PBS":
        return PBS(hpcType.upper())
    else:
        return None
