class Logout {
    static onGoogleSignIn() {
        console.log("Signed in to google");
        const auth2 = gapi.auth2.getAuthInstance();
        auth2.signOut().then(function () {
            Logout.allLoggedOut();
        });
    }

    static onGoogleLoginFail(error) {
        console.log("Could not sign in to google");
        console.log(error);

        Logout.allLoggedOut();
    }

    static allLoggedOut() {
        window.location.replace("/");
    }
}
