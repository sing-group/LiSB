last_timestamp = Date.now()

document.addEventListener(
    "DOMContentLoaded",
    function (event) {
        logs_div = document.getElementById('logs')
        logs_div.innerHTML = "<p>There aren't any logs yet</p>"
        do_ajax_query()
    }
)

function do_ajax_query() {
    $.ajax({
        url: '/monitor/real-time/' + last_timestamp,
        success: function (last_logs) {
            update_logs(last_logs)
        },
        complete: function () {
            // Schedule the next request when the current one's complete
            setTimeout(do_ajax_query, 10000);
        }
    });
}

function update_logs(last_logs) {

    if (last_logs.length !== 0) {
        last_timestamp_str = last_logs[last_logs.length - 1].substring(2, 25)
        last_timestamp = parse_datetime(last_timestamp_str)
        for (let log of last_logs) {
            var new_log_p = document.createElement('p')
            new_log_p.innerText = log
            logs_div.appendChild(new_log_p)
        }
    }
}

function parse_datetime(to_parse) {
    utc = to_parse.replace(" ", "T")
    splitted = utc.split(",")
    return Date.parse(splitted[0]) + parseInt(splitted[1])
}