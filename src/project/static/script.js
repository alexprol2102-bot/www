$(document).ready(function(){
    function showBanner(text) {
        $('#promo-banner').stop(true, true).text(text).slideDown().delay(5000).slideUp();
    }

    $('#67').on('submit',function(e){
        e.preventDefault();
        $.ajax({
            url: '/user_register',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                name: $('#fullname').val(),
                password: $('#password').val(),
                email: $('#email').val()
            }),
            success: function(response) {
                if(response.result) {
                    window.location.href = '/lk'; // Перенаправление при успехе
                } else {
                    alert('Ошибка регистрации! Возможно, Email уже занят.');
                }
            }
        });
    });

   $('#lg').on('submit',function(e){
        e.preventDefault();
        $.ajax({
            url: '/user_login',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                uname: $('#username').val(),
                p_hash: $('#password').val() 
            }),
            success: function(response) {
                if(response.result) {
                    window.location.href = '/lk'; // Перенаправление при успехе
                } else {
                    alert('Неверный логин или пароль!');
                }
            }
        });
    });

    // Обработка кнопки "Пополнить баланс"
    $('#topup-btn').on('click', function() {
        $.ajax({
            url: '/topup',
            method: 'POST',
            success: function(response) {
                if (response.result) {
                    $('.balance-value').html(response.new_balance + '<span class="currency">₽</span>');
                    showBanner('🎄 Новогодние скидки! +1000 ₽ на баланс');
                } else {
                    alert('Ошибка: ' + response.error);
                }
            }
        });
    });

    // Обработка кнопки "Сделать запрос"
    $('#make-request-btn').on('click', function() {
        $.ajax({
            url: '/make_request',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ text: $('#request-text').val() }),
            success: function(response) {
                if (!response.result) {
                    showBanner(response.error);
                    return;
                }
                $('.balance-value').html(response.new_balance + '<span class="currency">₽</span>');

                if (response.penalty) {
                    showBanner('За невнимательность -5000 ₽');
                } else {
                    $('#fullscreen-msg').css('display', 'flex').hide().fadeIn();
                    setTimeout(function() { $('#fullscreen-msg').fadeOut(); }, 3000);
                }
            }
        });
    });

    $('#fullscreen-msg').on('click', function() {
        $(this).fadeOut();
    });
});