var last_timestamp = Date.now()
var logs_div;
var status_msg;

document.addEventListener(
    "DOMContentLoaded",
    function (event) {
        do_monitoring_ajax_query();
        logs_div = document.getElementById('real-time-logs');
        status_button = document.getElementById('status-button');
        status_msg = document.getElementById('status-msg');
    }
)

function do_monitoring_ajax_query() {
    $.ajax({
        type: "GET",
        url: '/ajax/real-time-monitor/' + last_timestamp,
        success: function (last_logs) {
            update_logs(last_logs);
        },
        complete: function () {
            // Schedule the next request when the current one's complete
            setTimeout(do_monitoring_ajax_query, 1000);
        }
    });
}

function update_logs(last_logs) {

    if (last_logs.length !== 0) {

        // Remove no logs yet message if it hasn't been removed yet
        no_logs_msg = document.getElementById('no-logs-yet-msg');
        if (no_logs_msg !== null) {
            no_logs_msg.remove();
        }

        // Append logs by parts in p with spans
        let log;
        for (log of last_logs) {
            let new_log_div = document.createElement('div');
            for (let key of ['timestamp', 'level', 'module_and_thread']) {

                let span = document.createElement('span');
                span.innerText = `[ ${log[key]} ]`;
                classes = key;
                if (key === "level") {
                    class_name = " level-" + log['level'].toLowerCase();
                    classes += class_name;
                }
                span.classList = classes;
                new_log_div.appendChild(span)
            }

            // Add message
            let msg_span = document.createElement('span');
            msg_span.classList.add('msg')
            msg_span.innerText = log['msg'];
            new_log_div.appendChild(msg_span)

            logs_div.appendChild(new_log_div);
            // Update scroll
            logs_div.scrollTop = logs_div.scrollHeight
        }

        // Update last time with last timestamp
        last_timestamp = parse_datetime(log['timestamp']);
    }
}

function parse_datetime(to_parse) {
    utc = to_parse.replace(" ", "T");
    splitted = utc.split(",");
    return Date.parse(splitted[0]) + parseInt(splitted[1]);
}


function do_start_ajax_query() {
    $.ajax({
        type: "POST",
        url: '/ajax/start',
        success: function () {
            status_button.onclick = do_stop_ajax_query;
            status_button.innerHTML = "Stop Server";
            status_button.classList.remove('btn-success');
            status_button.classList.add('btn-danger');
            status_msg.innerHTML = "RUNNING";
        }
    });
}

function do_stop_ajax_query() {
    $.ajax({
        type: "POST",
        url: '/ajax/stop',
        success: function () {
            running = false;
            status_button.onclick = do_start_ajax_query;
            status_button.innerHTML = "Start Server";
            status_button.classList.remove('btn-danger');
            status_button.classList.add('btn-success');
            status_msg.innerHTML = "NOT RUNNING";
        }
    });
}