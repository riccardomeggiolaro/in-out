<svelte:head>
	<title>Dashboard</title>
	<meta name="description" content="About this app" />
</svelte:head>

<div class="content">
    <div>
        <span>000000</span>
        <span>kg</span>
    </div>
    <div>
        <div>
            000000
        </div>
        <div>
            ST
        </div>
    </div>
</div>

<div class="banner">

</div>

<style>
    div {
        border: 2px solid black;
        border-radius: 15px;
        margin: 3px;
    }

    .content,
    .banner {
        width: 100%;
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-content: center;
    }

    .content,
    .banner {
        border: 0px;
        margin: 0px;        
    }

    .content > div:last-child {
        border: 0px;
        margin-bottom: 0px;
        margin-top: 0px;
    }

    .content {
        height: 50vh;
    }

    .banner {
        height: 50vh;
    }

    .content div:first-child {
        width: 75%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
    }

    .content div:first-child span:first-child {
        font-size: 20vw;
        font-weight: bold;
        margin-bottom: 80px !important;
    }

    .content div:first-child span:last-child {
        position: absolute; 
        bottom: 0; 
        right: 0; 
        font-size: 4.5vw;
        font-weight: 500;
    }

    .content div:last-child {
        width: 25%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .content div:first-child div:last-child {
        width: 100%;
        height: 30vh;
        font-size: 2.5vw;
        font-weight: 500;
    }
    
    .content div:last-child div {
        width: 100%;
        height: 50vh;
        font-size: 6.5vw;
        font-weight: 500;
    }

    table {
        border: 1px solid black;
        width: 100%;
    }

    td div {
        width: 10px;
        height: 10px;
        background-color: green;
        border-radius: 100%;
    }
</style>