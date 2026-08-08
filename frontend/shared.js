/**
 * AgroRisk Advisor Shared Logic
 * Handles: navigation highlighting, theme detection & toggle.
 */
(function SharedUI() {
    "use strict";

    /* =================================================================
       1. Navigation Highlighting
       ================================================================= */
    const navLinks = document.querySelectorAll(".nav__link");
    const currentPath = window.location.pathname;

    navLinks.forEach((link) => {
        const href = link.getAttribute("href");
        const isHome = (currentPath === "/" || currentPath.endsWith("index.html")) && href === "index.html";
        const isOther = href !== "index.html" && currentPath.endsWith(href);

        if (isHome || isOther) {
            link.classList.add("nav__link--active");
            link.setAttribute("aria-current", "page");
        } else {
            link.classList.remove("nav__link--active");
            link.removeAttribute("aria-current");
        }
    });



})();
