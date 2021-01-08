class Logout {
    onGoogleLoginSucc() {
        console.log("Signed in to google");
        const auth2 = gapi.auth2.getAuthInstance();
        const t = this;
        auth2.signOut().then(function () {
            t.allLoggedOut();
        });
    }

    onGoogleLoginFail(error) {
        console.log("Could not sign in to google");
        console.log(error);

        this.allLoggedOut();
    }

    allLoggedOut() {
        window.location.replace("/");
    }
}

export default Logout;
