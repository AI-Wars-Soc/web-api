import Cookies from "js-cookie";
import $ from "jquery";

const COOKIE_NAME = 'CUWAIS_THEME';

class Style {
    constructor() {
        this.bootswatchLight = $("#bootswatch-light");
        this.bootswatchDark = $("#bootswatch-dark");
        this.bootswatchActive = $("#bootswatch-active");
    }

    copyRef(source) {
        this.bootswatchActive.attr({
            integrity: source.attr('integrity'),
            href: source.attr('href')
        });
    }

    setLight() {
        this.copyRef(this.bootswatchLight);

        Cookies.set(COOKIE_NAME, 'light');
    }

    setDark() {
        this.copyRef(this.bootswatchDark);

        Cookies.set(COOKIE_NAME, 'dark');
    }

    loadTheme() {
        const theme = Cookies.get(COOKIE_NAME);
        switch (theme) {
            case 'light':
                this.setLight();
                break;
            case 'dark':
                this.setDark();
                break;
            default:
                this.setLight();
                break;
        }
    }
}

export default Style;
