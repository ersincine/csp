import os
import shutil
import sys
import copy


class Course:

    def __init__(self, name, instructor, num_students, num_hours):
        self.name = name
        self.instructor = instructor
        self.num_students = num_students
        self.num_hours = num_hours
        self.start_time = None
        self.classroom = None

    @staticmethod
    def from_string(string):
        values = string.split(",")
        return Course(values[0], values[1], int(values[2]), int(values[3]))
    
    def __str__(self):
        return f"{self.name},{self.instructor},{self.num_students},{self.num_hours}"
    

class Classroom:

    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity

    @staticmethod
    def from_string(string):
        values = string.split(",")
        return Classroom(values[0], int(values[1]))
    
    def __str__(self):
        return f"{self.name},{self.capacity}"
    

class Preference:

    def __init__(self, instructor, times_available):
        self.instructor = instructor
        self.times_available = times_available

    @staticmethod
    def from_string(string):
        instructor, times_available = string.split(",")
        return Preference(instructor, set(times_available.split(" ")))
    
    def __str__(self):
        return f"{self.instructor},{' '.join(self.times_available)}"
    

class Coordination:

    def __init__(self, courses):
        self.courses = courses

    @staticmethod
    def from_string(string):
        return Coordination(set(string.split(" ")))
    
    def __str__(self):
        return ' '.join(self.courses)


def overlaps(start_time1, num_hours1, start_time2, num_hours2):
    # e.g. start_time1 = "Mon1", num_hours1 = 2, start_time2 = "Mon2", num_hours2 = 3
    assert start_time1 is not None
    assert start_time2 is not None
    day1 = start_time1[:3]
    day2 = start_time2[:3]
    if day1 != day2:
        return False  # Not on the same day
    start_hour1 = int(start_time1[3])
    start_hour2 = int(start_time2[3])
    end_hour1 = start_hour1 + num_hours1 - 1
    end_hour2 = start_hour2 + num_hours2 - 1
    if end_hour1 < start_hour2 or start_hour1 > end_hour2:
        return False  # Finished before or started after
    return True


def is_interrupted_by_lunch_break(start_hour, end_hour):
    assert isinstance(start_hour, int)
    assert isinstance(end_hour, int)
    return start_hour <= 4 < end_hour  # 4th hour is the end of the morning session


def can_assign(courses, course_idx, start_time_idx, classroom_idx):
    global classrooms
    global preferences
    global coordinations
    global times

    course = courses[course_idx]
    start_time = times[start_time_idx]
    classroom_name = classrooms[classroom_idx].name
    classroom_capacity = classrooms[classroom_idx].capacity

    # Exclusive Classroom Assignment
    other_courses_in_classroom = [c for c in courses if c.classroom == classroom_name]
    for other_course in other_courses_in_classroom:
        assert other_course.start_time is not None
        if overlaps(start_time, course.num_hours, other_course.start_time, other_course.num_hours):
            return False

    # Capacity Compliance
    if course.num_students > classroom_capacity:
        return False

    # Instructor Availability
    other_courses_with_instructor = [c for c in courses if c.instructor == course.instructor]
    for other_course in other_courses_with_instructor:
        if other_course.start_time is None:
            continue
        if overlaps(start_time, course.num_hours, other_course.start_time, other_course.num_hours):
            return False
        
    # Consecutive Scheduling
    day = start_time[:3]
    start_hour = int(start_time[3:])
    end_hour = start_hour + course.num_hours - 1
    end_time = f"{day}{end_hour}"
    if end_time not in times:  # e.g. "Mon9"
        return False
    if is_interrupted_by_lunch_break(start_hour, end_hour):
        return False
    
    # Instructor Preferences Compliance
    instructor_preferences = [p for p in preferences if p.instructor == course.instructor]
    assert len(instructor_preferences) <= 1
    if len(instructor_preferences) == 1:
        instructor_preference = instructor_preferences[0]
        for hour in range(start_hour, end_hour + 1):
            if f"{day}{hour}" not in instructor_preference.times_available:
                return False

    # Coordination Restrictions
    for coordination in coordinations:
        if course.name in coordination.courses:
            for other_course_name in coordination.courses:
                if other_course_name == course.name:
                    continue
                other_courses = [c for c in courses if c.name == other_course_name]
                assert len(other_courses) == 1
                other_course = other_courses[0]
                if other_course.start_time is None:
                    continue
                if overlaps(start_time, course.num_hours, other_course.start_time, other_course.num_hours):
                    return False

    return True


def solve_backtracking(course_idx):
    global courses
    global classrooms
    global preferences
    global coordinations
    global times
    global solutions

    # Base case: All courses have been assigned
    if course_idx == len(courses):
        solutions.append(copy.deepcopy(courses))
        return 

    for start_time_idx, start_time in enumerate(times):
        for classroom_idx, classroom in enumerate(classrooms):
            if can_assign(courses, course_idx, start_time_idx, classroom_idx):
                course = courses[course_idx]
                course.start_time = start_time
                course.classroom = classroom.name

                solve_backtracking(course_idx + 1)
                
                course.start_time = None
                course.classroom = None


def main(input_dir, output_dir):
    global courses 
    global classrooms
    global preferences
    global coordinations
    global times
    global solutions

    with open(os.path.join(input_dir, "courses.csv")) as f:
        courses = [Course.from_string(line.strip()) for line in f.readlines()[1:]]

    with open(os.path.join(input_dir, "classrooms.csv")) as f:
        classrooms = [Classroom.from_string(line.strip()) for line in f.readlines()[1:]]

    with open(os.path.join(input_dir, "preferences.csv")) as f:
        preferences = [Preference.from_string(line.strip()) for line in f.readlines()[1:]]

    with open(os.path.join(input_dir, "coordinations.csv")) as f:
        coordinations = [Coordination.from_string(line.strip()) for line in f.readlines()[1:]]

    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    times = [f"{day}{hour}" for day in days for hour in range(1, 9)]  # ["Mon1", ...]

    solutions = []

    solve_backtracking(0)
    
    for i, solution_courses in enumerate(solutions, 1):
        with open(os.path.join(output_dir, f"{i}.csv"), "w") as f:
            f.write("Course,Time,Classroom\n")
            for course in sorted(solution_courses, key=lambda c: c.name):
                assert course.start_time is not None
                assert course.classroom is not None
                f.write(f"{course.name},{course.start_time},{course.classroom}\n")


if __name__ == "__main__":
    """
    if os.path.exists("solutions1"):
        shutil.rmtree("solutions1")
    os.mkdir("solutions1")

    main("problem1", "solutions1")
    """

    main(sys.argv[1], sys.argv[2])
