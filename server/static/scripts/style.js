const STYLE_COOKIE_NAME = 'CUWAIS_THEME';

class Style {
    static bootswatchLight = $("#bootswatch-light");
    static bootswatchDark = $("#bootswatch-dark");
    static bootswatchActive = $("#bootswatch-active");

    static copyRef(source) {
        Style.bootswatchActive.attr({
            integrity: source.attr('integrity'),
            href: source.attr('href')
        });
    }

    static setLight() {
        Style.copyRef(Style.bootswatchLight);

        Cookies.set(STYLE_COOKIE_NAME, 'light');
    }

    static setDark() {
        Style.copyRef(Style.bootswatchDark);

        Cookies.set(STYLE_COOKIE_NAME, 'dark');
    }

    static loadTheme() {
        const theme = Style.getTheme();
        switch (theme) {
            case 'light':
                Style.setLight();
                break;
            case 'dark':
                Style.setDark();
                break;
            default:
                Style.setLight();
                break;
        }
    }

    static getTheme() {
        return Cookies.get(STYLE_COOKIE_NAME);
    }
}

Style.loadTheme();
