const STYLE_COOKIE_NAME = 'CUWAIS_THEME';
const STYLE_COOKIE_ARGS = { sameSite:'strict' };

class Style {
    static bootswatchLight = $("#bootswatch-light");
    static bootswatchDark = $("#bootswatch-dark");
    static bootswatchActive = $("#bootswatch-active");
    static styleLight = $("#style-light");
    static styleDark = $("#style-dark");
    static styleActive = $("#style-active");

    static copyRef(source, target) {
        target.attr({
            integrity: source.attr('integrity'),
            href: source.attr('href')
        });
    }

    static setLight() {
        Style.copyRef(Style.bootswatchLight, Style.bootswatchActive);
        Style.copyRef(Style.styleLight, Style.styleActive);

        Cookies.set(STYLE_COOKIE_NAME, 'light', STYLE_COOKIE_ARGS);
    }

    static setDark() {
        Style.copyRef(Style.bootswatchDark, Style.bootswatchActive);
        Style.copyRef(Style.styleDark, Style.styleActive);

        Cookies.set(STYLE_COOKIE_NAME, 'dark', STYLE_COOKIE_ARGS);
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
