import React from "react";
import ReactDOM from "react-dom";
import 'bootstrap';
import Login from "./login";
import Style from "./style";
import Logout from "./logout";

window.Login = new Login();
window.Logout = new Logout();
window.Style = new Style();

window.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM fully loaded and parsed');
});

window.Style.loadTheme();
