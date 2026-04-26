<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Akademik Informatika UII</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-white h-screen relative font-sans">


    <button id="chat-toggle"
        class="fixed bottom-6 right-6 w-14 h-14 bg-black text-white rounded-full shadow-2xl flex items-center justify-center hover:bg-gray-800 transition-all z-50 focus:outline-none hover:scale-105">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
            class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.48.432.447.74 1.04.586 1.641a4.483 4.483 0 01-.923 1.785A5.969 5.969 0 006 21c1.282 0 2.47-.402 3.445-1.087.81.22 1.668.337 2.555.337z" />
        </svg>
    </button>

    <div id="chat-window"
        class="hidden fixed bottom-24 right-6 w-80 sm:w-[380px] h-[550px] bg-white border border-gray-200 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden transition-all">

        <div class="bg-black text-white p-4 flex justify-between items-center shadow-sm">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                    <span class="text-black font-bold text-xs">UII</span>
                </div>
                <div>
                    <h3 class="font-semibold text-sm">Asisten Akademik UII</h3>
                    <p class="text-xs text-gray-300">Online</p>
                </div>
            </div>
            <button id="close-chat" class="text-gray-400 hover:text-white transition-colors focus:outline-none">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2"
                    stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>

        <main id="chat-container" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            <div class="flex justify-start">
                <div
                    class="bg-white border border-gray-200 text-black p-3 rounded-2xl rounded-tl-sm shadow-sm max-w-[85%] text-sm">
                    Halo! Saya asisten akademik Informatika UII. Ada yang bisa saya bantu terkait info KRS, syarat
                    lulus, atau beasiswa?
                </div>
            </div>
        </main>

        <div class="bg-white p-3 border-t border-gray-200">
            <form id="chat-form" class="flex items-center gap-2">
                <input type="text" id="user-input" placeholder="Tanya sesuatu..."
                    class="flex-1 bg-gray-100 text-sm text-black rounded-full px-4 py-2.5 border border-transparent focus:outline-none focus:border-black focus:bg-white transition-colors"
                    autocomplete="off">

                <button type="submit"
                    class="bg-black text-white w-10 h-10 rounded-full flex items-center justify-center hover:bg-gray-800 transition-colors flex-shrink-0 focus:outline-none">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"
                        class="w-4 h-4 ml-1">
                        <path
                            d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                    </svg>
                </button>
            </form>
        </div>
    </div>

    <script>
        const chatToggle = document.getElementById('chat-toggle');
        const chatWindow = document.getElementById('chat-window');
        const closeChat = document.getElementById('close-chat');

        const chatContainer = document.getElementById('chat-container');
        const chatForm = document.getElementById('chat-form');
        const userInput = document.getElementById('user-input');

        // Logika Buka/Tutup Chat
        chatToggle.addEventListener('click', () => {
            chatWindow.classList.remove('hidden');
            chatWindow.classList.add('flex');
            userInput.focus(); // Otomatis fokus ke input text
        });

        closeChat.addEventListener('click', () => {
            chatWindow.classList.add('hidden');
            chatWindow.classList.remove('flex');
        });

        // Fungsi menambah gelembung pesan dengan tema Monokrom
        function addMessage(text, isUser = false) {
            const div = document.createElement('div');
            div.className = isUser ? 'flex justify-end' : 'flex justify-start';

            const innerDiv = document.createElement('div');
            // Warna disesuaikan dengan tema Hitam Putih
            innerDiv.className = isUser
                ? 'bg-black text-white p-3 rounded-2xl rounded-tr-sm shadow-sm max-w-[85%] text-sm'
                : 'bg-white border border-gray-200 text-black p-3 rounded-2xl rounded-tl-sm shadow-sm max-w-[85%] text-sm';
            innerDiv.innerText = text;

            div.appendChild(innerDiv);
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll ke bawah
        }

        // Logika Pengiriman Pesan
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = userInput.value.trim();
            if (!query) return;

            // Nonaktifkan tombol saat loading
            const submitBtn = chatForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-50', 'cursor-not-allowed');

            addMessage(query, true);
            userInput.value = '';

            // Tampilan animasi loading
            const loadingId = 'loading-' + Date.now();
            const loadingDiv = document.createElement('div');
            loadingDiv.id = loadingId;
            loadingDiv.className = 'flex justify-start';
            loadingDiv.innerHTML = '<div class="bg-white border border-gray-200 p-3 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-1 max-w-[85%]"><span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span><span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></span><span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span></div>';
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const response = await fetch('http://localhost:5000/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });

                const data = await response.json();
                document.getElementById(loadingId).remove();

                if (data.answer) {
                    addMessage(data.answer);
                } else {
                    addMessage('Maaf, terjadi kesalahan saat menghubungi server.');
                }
            } catch (error) {
                if (document.getElementById(loadingId)) {
                    document.getElementById(loadingId).remove();
                }
                addMessage('Maaf, tidak dapat terhubung ke server AI.');
                console.error(error);
            } finally {
                // Aktifkan kembali tombol
                submitBtn.disabled = false;
                submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                userInput.focus();
            }
        });
    </script>
</body>

</html>