#!/home/pzx/pzx/boot-tests/venv/bin/python

import os
import sys
from uuid import UUID


from gem5art.artifact.artifact import Artifact
from gem5art.run import gem5Run
from gem5art.tasks.tasks import run_joob_pool

experiments_repo = Artifact.registerArtifact(
    command = '''
        git clone git@github.com:gem5/gem5-resources.git
        cd gem5-resources
        git checkout 1fe56ffc94005
        cd src/spec-2006
        git init
        git remote add origin git@github.com:hustpzx/spec-experiment.git
    ''',
    typ = 'git repo',
    name =  'spec2006 Experiment',
    path = './',
    cwd = './',
    documentation = '''
        local repo to run spec 2006 experiments with gem5 full system mode;
        resources cloned from git@github.com:gem5/gem5-resources.git
    '''
)

gem5_repo = Artifact.registerArtifact(
    command = 'git clone git@github.com:gem5/gem5.git',
    typ = 'git repo',
    name = 'gem5',
    path = 'gem5/',
    cwd = './',
    documentation = 'cloned gem5 from github.com and checked out v20.1.0.4'
)

gem5_binary = Artifact.registerArtifact(
    command = '''
        cd gem5;
        git checkout v20.1.0.4;
        scons build/X86/gem5.opt -j8
    ''',
    typ = 'gem5 binary',
    name = 'gem5-20.1.0.4',
    cwd = 'gem5/',
    path = 'gem5/build/X86/gem5.opt',
    inputs = [gem5_repo,],
    documentation = 'gem5 binary based on V20.1.0.4'
)

packer = Artifact.registerArtifact(
    command = '''
        wget https://releases.hashicorp.com/packer/1.6.6/packer_1.6.6_linux_amd64.zip;
        unzip packer_1.6.6_linux_amd64.zip;
    ''',
    typ = 'binary',
    name = 'packer',
    path = 'disk-image/packer',
    cwd = 'disk-image',
    documentation = '''Program to build disk images, download from hashicorp.com'''
)

linux_binary = Artifact.registerArtifact(
    command = 'cp ~/pzx/boot-tests/linux/vmlinux-4.19.83 ./',
    name = 'vmlinux-4.19.83',
    typ = 'kernel',
    path = './vmlinux-4.19.83',
    cwd = './',
    inputs = [experiments_repo,],
    documentation = 'Kernel binary for 4.19.83 from previous project-boot-tests'
)

m5_binary = Artifact.registerArtifact(
    command = '''
        cd gem5/util/m5;
        scons build/x86/out/m5;
        ''',
    typ = 'binary',
    name = 'm5',
    path = 'gem5/util/m5/build/x86/out/m5',
    cwd = './',
    inputs = [gem5_repo,],
    documentation = 'm5 utility'
)

disk_image = Artifact.registerArtifact(
    command = '''
        ./packer validate spec-2006/spec-2006.json;
        ./packer build spec-2006/spec-2006.json;
    ''',
    typ = 'disk image',
    name = 'spec-2006',
    cwd = 'disk-image/'
    path = 'disk-image/spec-2006/spec-2006-image/spec-2006',
    inputs = [packer, experiments_repo, m5_binary,],
    documentation = 'Ubuntu server with SPEC 2006 installed, m5 binary installed and root auto login'
)

if __name__ == "__main__":
    cpus = ['kvm', 'atomic', 'o3', 'timing']
    benchmark_sizes = {
        'kvm' : ['test', 'ref'],
        'atomic' : ['test'],
        'o3' : ['test'],
        'timing' : ['test']
    }
    benchmarks = [
        "400.perlbench", "401.bzip2", "403.gcc", "410.bwaves", "416.gamess", "429.mcf", "433.milc", "434.zeusmp", "435.gromacs",
        "436.cactusADM", "437.leslie3d", "444.namd", "445.gobmk", "447.dealII", "450.soplex", "453.povray", "454.calculix", 
        "456.hmmer", "458.sjeng", "459.GemsFDTD", "462.libquantum", "464.h264ref", "465.tonto", "470.lbm", "471.omnetpp",
        "473.astar", "481.wrf", "482.sphinx3", "482.xalancbmk", "998.specrand", "999.specrand"
    ]
    runs = []
    for cpu in cpus:
        for size in benchmark_sizes[cpu]:
            for benchmark in benchmarks:
                run = gem5Run.createFSRun(
                    'gem5 v20.1.0.4 spec 2006 experiment', # name
                    'gem5/build/X86/gem5.opt',  # gem5_binary
                    'configs/run_spec.py',  # gem5 run script
                    'results/{}/{}/{}'.format(cpu, size, benchmarks), # relative_outdir
                    gem5_binary,    #gem5 artifact
                    gem5_repo,  # gem5_git artifact
                    #run_script_repo,
                    'vmlinux-4.19.83', # linux binary
                    'disk-image/spec-2006/spec-2006-image/spec-2006', # disk-image
                    linux_binary,
                    disk_image,
                    cpu, benchmark, size, #params
                    timeout = 24*60*60  # 1 day
                )
                runs.append(run)

    run_joob_pool(runs)