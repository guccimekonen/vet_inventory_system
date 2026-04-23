document.addEventListener("DOMContentLoaded", function () {
    const resultWrappers = document.querySelectorAll(".change-list .results");

    resultWrappers.forEach((resultsWrapper) => {
        let isDown = false;
        let startX = 0;
        let scrollLeft = 0;

        resultsWrapper.addEventListener("mousedown", function (e) {
            isDown = true;
            resultsWrapper.classList.add("dragging");
            startX = e.pageX - resultsWrapper.offsetLeft;
            scrollLeft = resultsWrapper.scrollLeft;
        });

        resultsWrapper.addEventListener("mouseleave", function () {
            isDown = false;
            resultsWrapper.classList.remove("dragging");
        });

        resultsWrapper.addEventListener("mouseup", function () {
            isDown = false;
            resultsWrapper.classList.remove("dragging");
        });

        resultsWrapper.addEventListener("mousemove", function (e) {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - resultsWrapper.offsetLeft;
            const walk = (x - startX) * 1.5;
            resultsWrapper.scrollLeft = scrollLeft - walk;
        });
    });
});
