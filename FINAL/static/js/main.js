// Gestion des messages flash
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Calcul automatique du montant USDT
    const montantXafInput = document.getElementById('montant_xaf');
    const tauxVenteInput = document.getElementById('taux_vente');
    const montantUsdtSpan = document.getElementById('montant_usdt');
    
    if (montantXafInput && tauxVenteInput && montantUsdtSpan) {
        function calculateUSDT() {
            const montantXaf = parseFloat(montantXafInput.value) || 0;
            const tauxVente = parseFloat(tauxVenteInput.value) || 600;
            const montantUsdt = montantXaf / tauxVente;
            montantUsdtSpan.textContent = montantUsdt.toFixed(2);
        }
        
        montantXafInput.addEventListener('input', calculateUSDT);
        calculateUSDT();
    }
    
    // Calcul automatique du montant XAF pour la vente
    const montantUsdtInput = document.getElementById('montant_usdt_input');
    const tauxAchatInput = document.getElementById('taux_achat');
    const montantXafSpan = document.getElementById('montant_xaf_result');
    
    if (montantUsdtInput && tauxAchatInput && montantXafSpan) {
        function calculateXAF() {
            const montantUsdt = parseFloat(montantUsdtInput.value) || 0;
            const tauxAchat = parseFloat(tauxAchatInput.value) || 600;
            const montantXaf = montantUsdt * tauxAchat;
            montantXafSpan.textContent = montantXaf.toLocaleString('fr-FR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
        
        montantUsdtInput.addEventListener('input', calculateXAF);
        calculateXAF();
    }
    
    // Copier l'adresse wallet
    document.querySelectorAll('.copy-wallet').forEach(button => {
        button.addEventListener('click', function() {
            const address = this.getAttribute('data-address');
            navigator.clipboard.writeText(address).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copié';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });
    
    // Gestion du paiement
    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const amount = document.getElementById('payment-amount').value;
            const merchant = document.getElementById('merchant-number').textContent;
            
            const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
            modal.show();
        });
    }
    
    // Formatage des montants
    document.querySelectorAll('.format-amount').forEach(element => {
        const amount = parseFloat(element.textContent);
        if (!isNaN(amount)) {
            element.textContent = amount.toLocaleString('fr-FR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    });
    
    // Validation de l'adresse wallet
    const walletInput = document.getElementById('adresse_wallet');
    if (walletInput) {
        walletInput.addEventListener('input', function() {
            const address = this.value;
            const network = document.getElementById('reseau');
            const networkHelp = document.getElementById('network-help');
            
            if (address.startsWith('T')) {
                network.value = 'TRC20';
                if (networkHelp) networkHelp.textContent = 'Réseau détecté: TRC20 (Tron)';
            } else if (address.startsWith('0x')) {
                network.value = 'ETHEREUM';
                if (networkHelp) networkHelp.textContent = 'Réseau détecté: Ethereum';
            } else if (address.length === 44 && /^[A-Za-z0-9]+$/.test(address)) {
                network.value = 'SOL';
                if (networkHelp) networkHelp.textContent = 'Réseau détecté: Solana';
            } else if (address.toUpperCase().includes('TON')) {
                network.value = 'USDT_TON';
                if (networkHelp) networkHelp.textContent = 'Réseau détecté: USDT_TON';
            } else if (address.toUpperCase().includes('APT')) {
                network.value = 'USDT_APTOS';
                if (networkHelp) networkHelp.textContent = 'Réseau détecté: USDT_APTOS';
            }
        });
    }
});