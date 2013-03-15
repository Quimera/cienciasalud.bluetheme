(function($) {
    "use strict";

    $(document).ready(function() {

        $("img.lazy, img.lazy-hidden").lazyload({
            effect: "fadeIn"
        });

    });
})(jQuery);
