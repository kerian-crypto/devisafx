document.addEventListener('DOMContentLoaded', function() {
    const calculateForm = document.getElementById('calculate-form');
    const resultDiv = document.getElementById('calculate-result');
    const errorDiv = document.getElementById('calculate-error');
    
    if (calculateForm) {
        calculateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(calculateForm);
            const type = formData.get('type_calcul');
            const taux = parseFloat(formData.get('taux_mondial'));
            const benefice = parseFloat(formData.get('benefice'));
            const montant = parseFloat(formData.get('montant'));
            
            // Réinitialiser
            resultDiv.style.display = 'none';
            errorDiv.style.display = 'none';
            
            // Validation
            if (!taux || !benefice || !montant) {
                showError('Veuillez remplir tous les champs');
                return;
            }
            
            if (type === 'vente') {
                if (montant < 5000) {
                    showError('Le montant doit être supérieur ou égal à 5000 XAF pour la vente');
                    return;
                }
                if (montant >= 500000) {
                    showError('Le montant doit être inférieur à 500000 XAF pour la vente');
                    return;
                }
                
                // Calcul simplifié pour l'exemple
                let frais = 0;
                if (5000 <= montant && montant < 300000) {
                    frais = montant * 0.0151;
                } else if (300000 <= montant && montant < 500000) {
                    frais = montant * 0.01;
                }
                
                const tauxFinal = taux + benefice;
                const fraisParUsdt = frais / tauxFinal;
                const tauxAvecFrais = tauxFinal + fraisParUsdt;
                const usdtSansFrais = montant / tauxFinal;
                const usdtFinal = montant / tauxAvecFrais;
                
                showResult({
                    type: 'vente',
                    tauxFinal: tauxFinal.toFixed(2),
                    tauxAvecFrais: tauxAvecFrais.toFixed(2),
                    fraisOperateur: frais.toFixed(2),
                    fraisParUsdt: fraisParUsdt.toFixed(2),
                    usdtSansFrais: usdtSansFrais.toFixed(2),
                    usdtFinal: usdtFinal.toFixed(2)
                });
                
            } else {
                if (montant < 1) {
                    showError('Le montant doit être supérieur ou égal à 1 USDT pour l\'achat');
                    return;
                }
                if (montant >= 1000) {
                    showError('Le montant doit être inférieur à 1000 USDT pour l\'achat');
                    return;
                }
                
                // Calcul simplifié pour l'exemple
                let frais = 0;
                if (1 <= montant && montant < 500) {
                    frais = montant * 0.0151;
                } else if (500 <= montant && montant < 1000) {
                    frais = montant * 0.1;
                }
                
                const tauxFinal = taux - benefice;
                const fraisParUsdt = frais / tauxFinal;
                const tauxAvecFrais = tauxFinal - fraisParUsdt;
                const xafSansFrais = montant * tauxFinal;
                const xafFinal = montant * tauxAvecFrais;
                
                showResult({
                    type: 'achat',
                    tauxFinal: tauxFinal.toFixed(2),
                    tauxAvecFrais: tauxAvecFrais.toFixed(2),
                    fraisOperateur: frais.toFixed(2),
                    fraisParUsdt: fraisParUsdt.toFixed(2),
                    xafSansFrais: xafSansFrais.toFixed(2),
                    xafFinal: xafFinal.toFixed(2)
                });
            }
        });
    }
    
    function showResult(data) {
        let html = '';
        
        if (data.type === 'vente') {
            html = `
                <h5>Résultats du calcul (Vente USDT)</h5>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Sans frais opérateur</h6>
                                <p class="card-text">USDT obtenus: <strong>${data.usdtSansFrais}</strong></p>
                                <p class="card-text">Taux appliqué: <strong>${data.tauxFinal} XAF</strong></p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Avec frais opérateur</h6>
                                <p class="card-text">USDT obtenus: <strong>${data.usdtFinal}</strong></p>
                                <p class="card-text">Taux appliqué: <strong>${data.tauxAvecFrais} XAF</strong></p>
                                <p class="card-text">Frais opérateur: <strong>${data.fraisOperateur} XAF</strong></p>
                                <p class="card-text small">Frais par USDT: ${data.fraisParUsdt} XAF</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            html = `
                <h5>Résultats du calcul (Achat USDT)</h5>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Sans frais opérateur</h6>
                                <p class="card-text">XAF obtenus: <strong>${data.xafSansFrais}</strong></p>
                                <p class="card-text">Taux appliqué: <strong>${data.tauxFinal} XAF</strong></p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">Avec frais opérateur</h6>
                                <p class="card-text">XAF obtenus: <strong>${data.xafFinal}</strong></p>
                                <p class="card-text">Taux appliqué: <strong>${data.tauxAvecFrais} XAF</strong></p>
                                <p class="card-text">Frais opérateur: <strong>${data.fraisOperateur} XAF</strong></p>
                                <p class="card-text small">Frais par USDT: ${data.fraisParUsdt} XAF</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        resultDiv.innerHTML = html;
        resultDiv.style.display = 'block';
    }
    
    function showError(message) {
        errorDiv.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        errorDiv.style.display = 'block';
    }
});