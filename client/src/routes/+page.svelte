<script>
    // @ts-nocheck

    import { onMount, afterUpdate } from 'svelte';

    let data = {
        status: undefined,
        type: undefined,
        net_weight: undefined,
        gross_weight: undefined,
        tare: undefined,
        unite_measure: undefined
    };

    let weightCell;
    let isLoaded = false;

    function adjustFontSize() {
        if (!weightCell) return;
        
        const cellWidth = weightCell.offsetWidth;
        const cellHeight = weightCell.offsetHeight;
        
        // Inizia con una dimensione del font più grande
        let fontSize = Math.min(cellWidth, cellHeight) * 0.9;
        weightCell.style.fontSize = `${fontSize}px`;
        
        while (weightCell.scrollWidth > cellWidth || weightCell.scrollHeight > cellHeight) {
            fontSize *= 0.9;
            weightCell.style.fontSize = `${fontSize}px`;
        }
    }

    onMount(() => {
        // Ottieni la base URL del dominio corrente
        let baseUrl = window.location.origin;

        baseUrl = baseUrl.replace(/^http/, (match) => match === 'http' ? 'ws' : 'wss');

        // Costruisci l'URL WebSocket
        const websocketUrl = `${baseUrl}/realtime?name=1&node=01`;

        const _data = new WebSocket(websocketUrl);

        _data.addEventListener('message', (e) => {
            data = JSON.parse(e.data);
        });

        isLoaded = true;
    });

    afterUpdate(() => {
        if (isLoaded) {
            adjustFontSize();
        }
    });
</script>

<svelte:head>
    <title>Dashboard</title>
    <meta name="description" content="About this app" />
</svelte:head>

{#if isLoaded}
<table id="myTable">
    <tbody>
        <tr>
            <td rowspan="2" class="weight" bind:this={weightCell}>
                {data.net_weight !== undefined ? data.net_weight : 'N/A'}
                <span class="unite-misure">
                    {data.unite_measure !== undefined ? data.unite_measure : 'N/A'}
                </span>
            </td>
            <td class="tare">
                {data.tare !== undefined ? data.tare : 'N/A'}
            </td>
        </tr>
        <tr>
            <td class="status">
                {data.status !== undefined ? data.status : 'N/A'}
            </td>
        </tr>
    </tbody>
</table>

<div class="banner">
    <h1>Ciao</h1>
</div>
{/if}

<style>
    table,
    .banner {
        width: 100%;
        height: 50vh;
    }
    table {
        border: 2px solid black;
        border-radius: 15px;
        background-color: aliceblue;
        table-layout: fixed;
    }
    td {
        border: 2px solid black;
        border-radius: 15px;
        box-sizing: border-box;
        overflow: hidden;
        text-align: center;
        white-space: nowrap;
        padding: 5px;
    }
    .weight {
        position: relative;
        text-align: center;
        overflow: hidden;
        width: 75%;
        line-height: 1;
    }
    .tare,
    .status {
        width: 25%;
        font-size: 6.5vw;
    }
    .unite-misure {
        position: absolute;
        bottom: 8px;
        right: 5px;
        font-size: 0.15em;
    }
</style>