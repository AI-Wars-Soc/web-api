function onGoogleLoginSucc() {
    console.log("Signed in to google");
    const auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
        allLoggedOut();
    });
}

function onGoogleLoginFail(error) {
    console.log("Could not sign in to google");
    console.log(error);

    allLoggedOut();
}

function allLoggedOut() {
    window.location.replace("/");
}