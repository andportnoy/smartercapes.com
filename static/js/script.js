function buildSelect2(value1) {
    var select2 = document.getElementById("select2");
    if (value1 == "default") {
        select2.disabled = true;
    } else {
        select2.disabled = false;
    }
}
