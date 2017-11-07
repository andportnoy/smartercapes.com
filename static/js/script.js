function buildSelect2(dept, depts_and_courses) {
    var select2 = document.getElementById("select2");
    var button = document.getElementById("button");
    resetSelect2();
    if (dept == "default") {
        button.disabled = true;
        select2.disabled = true;
    } else {
        courses = depts_and_courses[dept];
        for (var i = 0; i < courses.length; i++) {
            var courseNumber = courses[i];
            var option = document.createElement("option")
            var value = "/" + dept + "/" + courseNumber;
            option.setAttribute("value", value);
            var text = document.createTextNode(courseNumber);
            option.appendChild(text);

            select2.appendChild(option)
        }
        select2.disabled = false;
    }
}
function resetSelect2() {
    var select2 = document.getElementById("select2");
    // reset dropdown to default state (one "Courses..." option)
    select2.options.length = 0;
    var default_option = document.createElement("option");
    default_option.text = "Courses..."
    default_option.value = "default"
    select2.options.add(default_option);
}

function updateButton(select2Value) {
    var button = document.getElementById("button");
    if (select2Value == "default") {
        button.disabled = true;
    } else {
        button.disabled = false;
    }
    lastCourse = select2Value;
}
