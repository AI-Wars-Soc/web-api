bootswatchLight = $("#bootswatch-light");
bootswatchDark = $("#bootswatch-dark");
bootswatchActive = $("#bootswatch-active");

function copyRef(source) {
    bootswatchActive.attr({
        integrity: source.attr('integrity'),
        href: source.attr('href')
    });
}

function setLight() {
    copyRef(bootswatchLight);

    Cookies.set('theme', 'light');
}

function setDark() {
    copyRef(bootswatchDark);

    Cookies.set('theme', 'dark');
}

function loadTheme() {
    const theme = Cookies.get('theme');
    switch (theme) {
        case 'light':
            setLight();
            break;
        case 'dark':
            setDark();
            break;
        default:
            setLight();
            break;
    }
}

loadTheme();