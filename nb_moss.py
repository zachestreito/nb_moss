import sys, os, subprocess, stat, urllib.request, nbconvert
from os.path import exists
from pathlib import Path
from nbgrader.apps import NbGraderAPI
from traitlets.config import Config


course_dir = None


def check(*arg): # first arg = assignment name, second OPTIONAl arg = custom course dir
    # process args
    if len(arg) == 1:
        assignment_name = arg[0].replace(" ", "_")
        course_dir = (os.getcwd())
    elif len(arg) == 2:
        assignment_name = arg[0].replace(" ", "_")
        course_dir = arg[1]
        course_dir = os.path.expanduser(course_dir)
        os.chdir(course_dir) # change working directory for os commands
    else:
        sys.exit("Error: Incorrect number of arguments")

    # create api config
    config = Config()
    config.CourseDirectory.root = course_dir

    # initialize api with config
    nb_api = NbGraderAPI(config=config)

    # check for moss script, download if not found
    if not exists("%s/moss.pl" % course_dir):
        print("moss.pl not found.")
        print("Do you have a moss account (Y/n)?")
        moss_in = input()
        if (moss_in == "" or moss_in[0].lower() == "y"):
            user_id = input("Enter Moss UserID: ")
            if (len(user_id) != 9 or not user_id.isdecimal()):
                sys.exit("Invalid input. Exiting.")
            else:
                url = "http://moss.stanford.edu/general/scripts/mossnet"
                urllib.request.urlretrieve(url, "moss.pl")
                file = Path("%s/moss.pl" % course_dir)
                file.chmod(file.stat().st_mode | stat.S_IEXEC) # make moss.pl executable
                with open(file, 'r+') as f:
                    r = f.read().replace('987654321', user_id) # replace user id in moss.pl with input
                    f.seek(0)
                    f.write(r)
        elif moss_in[0].lower() == "n":
            sys.exit("You can find Moss registration instructions here: http://moss.stanford.edu/")
        else:
            sys.exit("Invalid input. Exiting.")


    # create set of students who have submitted assignment_name
    students = nb_api.get_submitted_students(assignment_name)
    if len(students) <= 0: # terminate if no submissions found
        sys.exit("Error: No submissions found for %s" % assignment_name)

    # retrieve list of all notebooks in assignment
    notebooks = (os.listdir("%s/release/%s/" % (course_dir, assignment_name)))
    for i in range(len(notebooks)):
        if notebooks[i].endswith('.ipynb'):
            notebooks[i] = notebooks[i][:-6] # remove file extension from string
        else: # remove item from list if it is not .ipynb 
            notebooks[i] = None # temporary change to none because we don't want to change array size in the middle of the loop
    notebooks = list(filter(None, notebooks)) # remove all null elements

    # create directories for converted files
    for notebook in notebooks:
        os.makedirs("moss/%s/%s/submissions/" % (assignment_name, notebook), exist_ok=True)

    # convert base files
    for notebook in notebooks:
        __convert("%s/release/%s/%s.ipynb" % (course_dir, assignment_name, notebook), "%s/moss/%s/%s/" % (course_dir, assignment_name, notebook), "base")

    # convert student submissions
    for student in students:
        for notebook in notebooks:
            file_path = ("%s/submitted/%s/%s/%s.ipynb" % (course_dir, student, assignment_name, notebook))
            if exists(file_path):
                __convert(file_path, "%s/moss/%s/%s/submissions/" % (course_dir, assignment_name, notebook), student)

    # SUBMIT!
    for notebook in notebooks:
        result = __submit(course_dir, assignment_name, notebook, students)
        # GRAPH IT!
        graph_command = 'mossum -p 70 -t ".*/(.+)" %s' % result
        cwd = os.getcwd()
        os.chdir("%s/moss/%s/%s" % (course_dir, assignment_name, notebook))
        os.system(graph_command)
        os.chdir(cwd)


# convert .ipynb assignments to trimmed .py
def __convert(input_file, output_dir, output_name):
    command = "jupyter nbconvert --output='%s%s' --to script %s" % (output_dir, output_name, input_file)
    os.system(command)


# submit files to moss
def __submit(course_dir, assignment_name, notebook, students):
    # Check file format of base file to identify programming language
    language = ""
    extension = ""
    if exists("%s/moss/%s/%s/base.py" % (course_dir, assignment_name, notebook)):
        language = "python"
        extension = "py"
    elif exists("%s/moss/%s/%s/base.cs" % (course_dir, assignment_name, notebook)):
        language = "csharp"
        extension = "cs"
    elif exists("%s/moss/%s/%s/base.cpp" % (course_dir, assignment_name, notebook)):
        language = "cc" #C++
        extension = "cpp"
    student_files = "%s/moss/%s/%s/base.%s" % (course_dir, assignment_name, notebook, extension)
    for student in students:
        student_files = student_files + (" %s/moss/%s/%s/submissions/%s.%s" % (course_dir, assignment_name, notebook, student, extension))
    command = ("%s/moss.pl -l %s -b %s" % (course_dir, language, student_files))
    #print(command)
    # Get the results url, decode it, and return it
    output = subprocess.check_output(command, shell=True)
    b_url = output.split(b'\n')
    for line in b_url:
        print(line.decode())
    url = b_url[-2].decode()
    return url