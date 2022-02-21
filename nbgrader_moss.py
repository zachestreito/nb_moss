import sys, os, stat, urllib.request, nbconvert
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
        if moss_in.lower() == "n":
            sys.exit("You can find Moss registration instructions here: http://moss.stanford.edu/")
        elif (moss_in[0].lower() == "y" or moss_in == ""):
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
        else:
            sys.exit("Invalid input. Exiting.")

    # create set of students who have submitted assignment_name
    student_set = nb_api.get_submitted_students(assignment_name)
    if len(student_set) <= 0: # terminate if no submissions found
        sys.exit("Error: No submissions found for %s" % assignment_name)

    # create directory for converted files
    os.makedirs("moss/%s/submissions/" % assignment_name, exist_ok=True)

    # convert base file
    __convert("%s/release/%s/%s.ipynb" % (course_dir, assignment_name, assignment_name), "%s/moss/%s/" % (course_dir, assignment_name), "base")

    # convert student submissions
    for student in student_set:
        __convert("%s/submitted/%s/%s/%s.ipynb" % (course_dir, student, assignment_name, assignment_name), "%s/moss/%s/submissions/" % (course_dir, assignment_name), student)

    # SUBMIT!
    __submit(course_dir, assignment_name)


# convert .ipynb assignments to trimmed .p
def __convert(input_file, output_dir, output_name):
    command = "jupyter nbconvert --output='%s%s' --to python %s" % (output_dir, output_name, input_file)
    os.system(command)


# submit files to moss
def __submit(course_dir, assignment_name):
    command = ("%s/moss.pl -l python -b %s/moss/%s/base.py -d %s/moss/%s/submissions/*.py" % (course_dir, course_dir, assignment_name, course_dir, assignment_name))
    os.system(command)