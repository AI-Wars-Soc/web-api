class Login {
    static googleInit() {
        gapi.load('auth2', function () {
            // Done
        });
    }

    static onGoogleSignIn(googleUser) {
        const id_token = googleUser.getAuthResponse().id_token;

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/login_google');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status !== 200) {
                Login.onLoginFail(xhr.responseText);
                return;
            }
            const error_message = $("#login-error-msg");
            error_message.hide();
            console.log('Signed in as: ' + xhr.responseText);
            location.reload();
        };
        xhr.onerror = function () {
            Login.onLoginFail(xhr.responseText);
        };
        xhr.send(JSON.stringify({
            idtoken: id_token
        }));
    }

    static onLoginFail(error) {
        console.log("Could not sign in");
        console.log(error);

        const error_message = $("#login-error-msg");
        error_message.show();
    }
}
