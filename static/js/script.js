"use strict";

/* =====================================================
   BLOOD DONOR AVAILABILITY MANAGEMENT SYSTEM
   Main JavaScript
===================================================== */


/* ---------- Mobile Navigation ---------- */

document.addEventListener("DOMContentLoaded", function () {

    const menuToggle = document.getElementById("menuToggle");
    const navLinks = document.getElementById("navLinks");

    if (menuToggle && navLinks) {

        menuToggle.addEventListener("click", function () {

            const isOpen = navLinks.classList.toggle("active");

            menuToggle.setAttribute(
                "aria-expanded",
                String(isOpen)
            );

            menuToggle.textContent = isOpen ? "✕" : "☰";
        });

        // Close menu after selecting a navigation link
        navLinks.querySelectorAll("a").forEach(function (link) {

            link.addEventListener("click", function () {

                navLinks.classList.remove("active");

                menuToggle.setAttribute(
                    "aria-expanded",
                    "false"
                );

                menuToggle.textContent = "☰";
            });

        });

    }


    /* ---------- Flash Message Close ---------- */

    document.querySelectorAll(".flash-close").forEach(
        function (button) {

            button.addEventListener("click", function () {

                const message = button.closest(".flash-message");

                if (message) {
                    message.remove();
                }

            });

        }
    );


    /* ---------- Automatically Hide Flash Messages ---------- */

    document.querySelectorAll(".flash-message").forEach(
        function (message) {

            window.setTimeout(function () {

                if (message.isConnected) {

                    message.style.transition = "opacity 0.4s ease";
                    message.style.opacity = "0";

                    window.setTimeout(function () {

                        if (message.isConnected) {
                            message.remove();
                        }

                    }, 450);

                }

            }, 5000);

        }
    );


    /* ---------- Password Confirmation ---------- */

    const registerForm = document.getElementById("registerForm");

    if (registerForm) {

        registerForm.addEventListener("submit", function (event) {

            const password = document.getElementById("password");
            const confirmPassword = document.getElementById(
                "confirm_password"
            );

            if (
                password &&
                confirmPassword &&
                password.value !== confirmPassword.value
            ) {

                event.preventDefault();

                alert("Passwords do not match.");

                confirmPassword.focus();
                return;
            }

            if (password && password.value.length < 8) {

                event.preventDefault();

                alert("Password must contain at least 8 characters.");

                password.focus();
            }

        });

    }


    /* ---------- Mobile Number Validation ---------- */

    const phoneInputs = document.querySelectorAll(
        'input[name="phone"], input[name="contact_phone"]'
    );

    phoneInputs.forEach(function (input) {

        input.addEventListener("input", function () {

            // Keep only numeric characters
            input.value = input.value
                .replace(/\D/g, "")
                .slice(0, 10);

        });

    });


    /* ---------- Blood Request Confirmation ---------- */

    const bloodRequestForm = document.getElementById(
        "bloodRequestForm"
    );

    if (bloodRequestForm) {

        bloodRequestForm.addEventListener(
            "submit",
            function (event) {

                const confirmed = window.confirm(
                    "Do you want to submit this blood request?"
                );

                if (!confirmed) {
                    event.preventDefault();
                }

            }
        );

    }


    /* ---------- Donor Form Validation ---------- */

    const donorForm = document.getElementById("donorForm");

    if (donorForm) {

        donorForm.addEventListener("submit", function (event) {

            const ageInput = document.getElementById("age");

            if (!ageInput) {
                return;
            }

            const age = Number(ageInput.value);

            if (
                !Number.isInteger(age) ||
                age < 18 ||
                age > 65
            ) {

                event.preventDefault();

                alert(
                    "Please enter a valid donor age between 18 and 65."
                );

                ageInput.focus();
            }

        });

    }


    /* ---------- Search Donor Form Validation ---------- */

    const searchDonorForm = document.getElementById(
        "searchDonorForm"
    );

    if (searchDonorForm) {

        searchDonorForm.addEventListener("submit", function (event) {

            const bloodGroup = document.getElementById("blood_group");
            const city = document.getElementById("city");

            const hasBloodGroup = bloodGroup &&
                bloodGroup.value.trim() !== "";

            const hasCity = city &&
                city.value.trim() !== "";

            if (!hasBloodGroup && !hasCity) {

                event.preventDefault();

                alert(
                    "Please select a blood group or enter a city."
                );

                if (bloodGroup) {
                    bloodGroup.focus();
                }
            }

        });

    }


    /* ---------- Logout Confirmation ---------- */

    document.querySelectorAll('a[href*="/logout"]').forEach(
        function (link) {

            link.addEventListener("click", function (event) {

                const confirmed = window.confirm(
                    "Are you sure you want to logout?"
                );

                if (!confirmed) {
                    event.preventDefault();
                }

            });

        }
    );


    /* ---------- Forms with Confirmation ---------- */

    document.querySelectorAll("form[data-confirm]").forEach(
        function (form) {

            form.addEventListener("submit", function (event) {

                const message = form.getAttribute("data-confirm");

                if (message && !window.confirm(message)) {
                    event.preventDefault();
                }

            });

        }
    );


    /* ---------- Prevent Double Form Submission ---------- */

    document.querySelectorAll(
        "form[data-prevent-double-submit]"
    ).forEach(function (form) {

        form.addEventListener("submit", function () {

            if (form.dataset.submitted === "true") {
                return;
            }

            form.dataset.submitted = "true";

            const submitButton = form.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Please wait...";
            }

        });

    });


    /* ---------- Search Input Trim ---------- */

    document.querySelectorAll(
        'form input[type="search"], form input[name="city"]'
    ).forEach(function (input) {

        input.addEventListener("blur", function () {
            input.value = input.value.trim();
        });

    });


    /* ---------- Current Year in Footer ---------- */

    const currentYear = document.getElementById("currentYear");

    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }


    console.log(
        "Blood Donor Management System JavaScript loaded successfully."
    );

});