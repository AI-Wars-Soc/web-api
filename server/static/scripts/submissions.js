const submission_error_box = $("#submission-error-msg");
const repo_box = $("#repo");
const bot_name_box = $("#bot-name");

class Submissions {
    static setSubmissionEnabledSwitch(v, id) {
        if (v.checked) {
            Submissions.set_enabled(id, true);
        } else {
            Submissions.set_enabled(id, false);
        }
    }

    static set_enabled(submission_id, enabled) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/set_submission_active');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status !== 200) {
                Submissions.onSetEnabledFail(xhr.responseText);
                return;
            }
            window.location.reload();
        };
        xhr.onerror = function () {
            Submissions.onSetEnabledFail(xhr.responseText);
        };
        xhr.send(JSON.stringify({
            submission_id: submission_id,
            enabled: enabled
        }));
    }

    static onSetEnabledFail(response_text) {
        console.log(response_text);
        const response = JSON.parse(response_text)
        submission_error_box.text(response.message);
        submission_error_box.show();
    }

    static onSubmit(e) {
        e.preventDefault();
        const url = repo_box.val();

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/add_submission');
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
}

$('#submission-form').submit(Submissions.onSubmit);
$('#bot-form').submit(Submissions.onBotSubmit);
