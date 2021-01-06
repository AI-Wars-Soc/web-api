function googleInit() {
    gapi.load('auth2', function () {
        // Done
    });
}

function onGoogleSignIn(googleUser) {
    const id_token = googleUser.getAuthResponse().id_token;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/login_google');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        if (xhr.status !== 200) {
            onLoginFail(xhr.responseText);
            return;
        }
        const error_message = $("#login-error-msg");
        error_message.hide();
        console.log('Signed in as: ' + xhr.responseText);
        location.reload();
    };
    xhr.onerror = function () {
        onLoginFail(xhr.responseText);
    };
    xhr.send(JSON.stringify({
        idtoken: id_token
    }));
}

function onLoginFail(error) {
    console.log("Could not sign in");
    console.log(error);

    const error_message = $("#login-error-msg");
    error_message.show();
}
