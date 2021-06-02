function send_form(form_name) {
    form = document.forms[form_name]
    form.submit()
}

document.addEventListener(
    "DOMContentLoaded",
    function (event) {
        $('input[type=radio][name=filter]').change(function () {
            var searchInput = document.getElementById("search-input");
            searchInput.name = this.value;
        });
    }
)