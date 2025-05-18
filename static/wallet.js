(function () {
    const providerOptions = {
        walletconnect: {
            package: window.WalletConnectProvider.default,
            options: {
                rpc: {
                    1: 'https://cloudflare-eth.com'
                },
            },
        },
        coinbasewallet: {
            package: window.CoinbaseWalletSDK,
            options: {
                appName: 'PodcastApp',
                rpc: 'https://cloudflare-eth.com',
                chainId: 1,
            },
        },
    };

    const web3Modal = new window.Web3Modal.default({
        cacheProvider: false,
        providerOptions,
    });

    const connectButton = document.getElementById('connect-wallet');
    if (!connectButton) return;

    connectButton.addEventListener('click', async () => {
        try {
            const instance = await web3Modal.connect();
            const provider = new ethers.providers.Web3Provider(instance);
            const signer = provider.getSigner();
            const address = await signer.getAddress();
            document.getElementById('wallet-info').innerText = 'Connected: ' + address;
        } catch (err) {
            console.error('Wallet connection failed', err);
        }
    });
})();
