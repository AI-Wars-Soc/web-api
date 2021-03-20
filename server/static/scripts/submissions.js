const submission_error_box = $("#submission-error-msg");
const repo_box = $("#repo");

class Submissions {
    static set_enabled(submission_id, enabled, callback) {
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

    static onSubmitFail(response_text) {
        console.log(response_text);
        const response = JSON.parse(response_text)
        submission_error_box.text(response.message);
        repo_box.effect("shake");
        submission_error_box.show();
    }
}

$('#submission-form').submit(Submissions.onSubmit);