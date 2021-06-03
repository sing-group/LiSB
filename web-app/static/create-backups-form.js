document.addEventListener(
    "DOMContentLoaded",
    function (event) {
        const s3_selector = document.getElementById('s3-upload')
        s3_selector.onchange = function () {
            manage_s3_section(this.selectedIndex)
        };
    }
)

function manage_s3_section(index) {
    const s3_params_div = document.getElementById('s3-params');
    if (index === 0) {
        s3_params_div.innerHTML = "";
    } else {
        to_create = {
            "s3-bucket-name": "Enter the S3 bucket name",
            "s3-bucket-path": "Enter the S3 bucket path"
        };
        for (const [name, label_txt] of Object.entries(to_create)) {
            // Create input element
            var input = document.createElement('input');
            input.type = "text";
            input.name = name;
            // Create label element for input
            var label = document.createElement('label');
            label.htmlFor = name;
            label.innerHTML = label_txt;
            // Create to append input and label to and append to section
            var div = document.createElement('div');
            div.appendChild(label)
            div.appendChild(input)
            s3_params_div.appendChild(div)
        }
    }
}