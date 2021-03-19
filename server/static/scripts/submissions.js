const submission_error_box = $("#submission-error-msg");

$('#submission-form').submit(function(e){
    e.preventDefault();
    const repo_box = $("#repo");
    const url = repo_box.val();
    $.post(
        {
            url: "/api/add_submission",
            data: JSON.stringify({url: url}),
            contentType: 'application/json',
            success: function(receivedData){
                let t = receivedData._cuwais_type;
                if (t === "submission") {
                    submission_error_box.hide();
                    repo_box.val("");
                    window.location.reload();
                } else if (t === "error") {
                    submission_error_box.text(receivedData.error_message);
                    repo_box.effect("shake");
                    submission_error_box.show();
                } else {
                    submission_error_box.text("Unknown return type: " + t + ". Please let Joe know");
                    submission_error_box.show();
                }
                console.log(receivedData);
            }
        }
    );
});