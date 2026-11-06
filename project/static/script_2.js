$(document).ready(function(){
    function showBanner(text) {
        $('#promo-banner').stop(true, true).text(text).slideDown().delay(5000).slideUp();
    }

    $('#register-form').on('submit', function(e) {
        e.preventDefault();
        const password = $('#password').val();
        const confirmPassword = $('#confirm_password').val();

        if (password !== confirmPassword) {
            alert('Пароли не совпадают!');
            return;
        }
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
                    window.location.href = '/lk';
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
                    window.location.href = '/lk';
                } else {
                    alert('Неверный логин или пароль!');
                }
            }
        });
    });

    $('#topup-btn').on('click', function() {
        $('#topupModal').fadeIn(200);
    });

    $('.close').on('click', function() {
        $('#topupModal').fadeOut(200);
    });

    $(window).on('click', function(event) {
        if ($(event.target).is('#topupModal')) {
            $('#topupModal').fadeOut(200);
        }
    });

    $('.quick-btn').on('click', function() {
        const amount = $(this).data('amount');
        $('#amount-input').val(amount);
    });

    $('#confirm-topup').on('click', function() {
        const amount = parseInt($('#amount-input').val());
        if (!amount || amount < 1 || amount > 10000) {
            alert('Введите сумму от 1 до 10000 рублей');
            return;
        }

        $.ajax({
            url: '/topup_balance',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ amount: amount }),
            success: function(response) {
                if(response.result) {
                    $('#balance-display').html(response.new_balance + '<span class="currency">₽</span>');
                    $('#topupModal').fadeOut(200);
                    $('#amount-input').val('');
                    showBanner('🎄 Баланс пополнен на ' + amount + ' ₽!');
                } else {
                    alert('Ошибка: ' + response.error);
                }
            }
        });
    });
});
