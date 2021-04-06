const submission_error_box = $("#submission-error-msg");
const repo_box = $("#repo");
const bot_name_box = $("#bot-name");
const submit_spinner = $("#submit-spinner")

class Submissions {
    static setSubmissionEnabledSwitch(checkbox, submission_id) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/set_submission_active');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            window.location.reload();
        };
        xhr.onerror = function () {
            console.log(xhr.responseText);
            const response = JSON.parse(xhr.responseText)
            submission_error_box.text(response.message);
            submission_error_box.show();
            Submissions.uncheck(checkbox, !checkbox.checked);
        };
        xhr.send(JSON.stringify({
            submission_id: submission_id,
            enabled: checkbox.checked
        }));
        window.setInterval(() => Submissions.uncheck(checkbox, !checkbox.checked), 3000);
    }

    static uncheck(checkbox, unchecked) {
        checkbox.checked = unchecked;
    }

    static onSubmit(e) {
        e.preventDefault();
        const url = repo_box.val();
        repo_box.val("");

        submit_spinner.show();

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/add_submission');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status !== 200) {
                Submissions.onSubmitFail(xhr.responseText);
                return;
            }
            const response = JSON.parse(xhr.responseText)
            if (response.status === "resent") { // Ignore resent requests
                return;
            }
            submission_error_box.hide();
            window.location.reload();
        };
        xhr.onerror = function () {
            Submissions.onSubmitFail(xhr.responseText);
        };
        xhr.send(JSON.stringify({
            url: url
        }));
    }

    static onBotSubmit(e) {
        e.preventDefault();
        const url = repo_box.val();
        const name = bot_name_box.val();

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/add_bot');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status !== 200) {
                Submissions.onSubmitFail(xhr.responseText);
                return;
            }
            submission_error_box.hide();
            repo_box.val("");
            window.location.reload();
        };
        xhr.onerror = function () {
            Submissions.onSubmitFail(xhr.responseText);
        };
        xhr.send(JSON.stringify({
            url: url,
            name: name
        }));
    }

    static onSubmitFail(response_text) {
        console.log(response_text);
        const response = JSON.parse(response_text)
        submission_error_box.text(response.message);
        repo_box.effect("shake");
        submission_error_box.show();
        submit_spinner.hide();
    }

    static deleteBot(id) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/remove_bot');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status !== 200) {
                Submissions.onSubmitFail(xhr.responseText);
                return;
            }
            window.location.reload();
        };
        xhr.onerror = function () {
            Submissions.onSubmitFail(xhr.responseText);
        };
        xhr.send(JSON.stringify({
            id: id
        }));
    }

    static makeGraph(id) {
        const canvas_id = 'submissionSummaryGraph' + id;
        const ctx = document.getElementById(canvas_id).getContext('2d');

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/get_submission_summary_graph');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            console.log(xhr.responseText);
        };
        xhr.onerror = function () {
            $("#" + canvas_id).hide();
            console.log(xhr.responseText);
        }
        xhr.send(JSON.stringify({
            submission_id: id
        }));
    }
}

$('#submission-form').submit(Submissions.onSubmit);
$('#bot-form').submit(Submissions.onBotSubmit);
