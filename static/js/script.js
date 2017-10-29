function buildSelect2(value1) {
    var select2 = document.getElementById("select2");
    console.log("value is");
    console.log(value1);
    if (value1 == "default") {
        select2.disabled = true;
    } else {
        select2.disabled = false;
    }
}
