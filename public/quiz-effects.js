(function(){
  if(location.pathname.replace(/\/+$/,'')!=='/quiz') return;

  const style=document.createElement('style');

  style.textContent=`
    .ed-celebration-layer{
      position:fixed;
      inset:0;
      width:100vw;
      height:100vh;
      pointer-events:none;
      overflow:hidden;
      z-index:99999;
      isolation:isolate;
    }

    /* ---------- CENTRAL BURST ---------- */

    .ed-celebration-burst{
      position:fixed;
      left:50%;
      top:42%;
      width:20px;
      height:20px;
      pointer-events:none;
      transform:translate(-50%,-50%);
    }

    .ed-celebration-ring{
      position:absolute;
      left:50%;
      top:50%;
      width:22px;
      height:22px;
      border:3px solid rgba(250,204,21,.95);
      border-radius:50%;
      transform:translate(-50%,-50%) scale(.2);
      opacity:0;
      animation:edRing .9s cubic-bezier(.16,.8,.25,1) forwards;
      box-shadow:
        0 0 18px rgba(250,204,21,.75),
        0 0 38px rgba(34,197,94,.35);
    }

    @keyframes edRing{
      0%{
        opacity:0;
        transform:translate(-50%,-50%) scale(.2);
      }
      18%{
        opacity:1;
      }
      70%{
        opacity:.8;
      }
      100%{
        opacity:0;
        transform:translate(-50%,-50%) scale(7);
      }
    }

    .ed-burst-spark{
      position:absolute;
      left:50%;
      top:50%;
      width:7px;
      height:15px;
      border-radius:999px;
      transform:
        translate(-50%,-50%)
        translate(0,0)
        rotate(0deg)
        scale(.35);
      opacity:0;
      animation:edSparkBurst .85s cubic-bezier(.15,.8,.25,1) forwards;
      box-shadow:0 0 10px currentColor;
    }

    @keyframes edSparkBurst{
      0%{
        opacity:0;
        transform:
          translate(-50%,-50%)
          translate(0,0)
          rotate(0deg)
          scale(.25);
      }
      12%{
        opacity:1;
      }
      100%{
        opacity:0;
        transform:
          translate(-50%,-50%)
          translate(var(--bx),var(--by))
          rotate(360deg)
          scale(1);
      }
    }

    /* ---------- CONFETTI ---------- */

    .ed-confetti{
      position:absolute;
      top:-28px;
      width:8px;
      height:15px;
      border-radius:3px;
      opacity:0;
      will-change:transform,opacity;
      animation:
        edConfettiFall
        var(--dur)
        cubic-bezier(.18,.72,.25,1)
        var(--delay)
        forwards;
    }

    .ed-confetti.round{
      width:9px;
      height:9px;
      border-radius:50%;
    }

    .ed-confetti.ribbon{
      width:5px;
      height:21px;
      border-radius:999px;
    }

    @keyframes edConfettiFall{
      0%{
        opacity:0;
        transform:
          translate3d(0,-30px,0)
          rotate(0deg)
          scale(.55);
      }

      7%{
        opacity:1;
      }

      35%{
        opacity:1;
        transform:
          translate3d(var(--x1),35vh,0)
          rotate(var(--r1))
          scale(1);
      }

      68%{
        opacity:.95;
        transform:
          translate3d(var(--x2),70vh,0)
          rotate(var(--r2))
          scale(.95);
      }

      100%{
        opacity:0;
        transform:
          translate3d(var(--x3),112vh,0)
          rotate(var(--r3))
          scale(.75);
      }
    }

    /* ---------- SMALL FLASH ---------- */

    .ed-celebration-flash{
      position:fixed;
      left:50%;
      top:42%;
      width:90px;
      height:90px;
      border-radius:50%;
      pointer-events:none;
      z-index:99998;
      transform:translate(-50%,-50%) scale(.15);
      opacity:0;
      background:
        radial-gradient(
          circle,
          rgba(255,255,255,.95) 0%,
          rgba(250,204,21,.45) 18%,
          rgba(34,197,94,.15) 42%,
          transparent 70%
        );
      animation:edFlash .7s ease-out forwards;
    }

    @keyframes edFlash{
      0%{
        opacity:0;
        transform:translate(-50%,-50%) scale(.15);
      }
      15%{
        opacity:.9;
      }
      100%{
        opacity:0;
        transform:translate(-50%,-50%) scale(2.4);
      }
    }

    /* IMPORTANT:
       No animation is applied to #quizResult.
       Therefore result + leaderboard cannot jump/pop/scroll.
    */

    @media(prefers-reduced-motion:reduce){
      .ed-confetti,
      .ed-burst-spark,
      .ed-celebration-ring,
      .ed-celebration-flash{
        animation:none!important;
        display:none!important;
      }
    }
  `;

  document.head.appendChild(style);

  let celebrated=false;

  function celebrate(){
    if(celebrated) return;
    celebrated=true;

    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){
      return;
    }

    const layer=document.createElement('div');
    layer.className='ed-celebration-layer';

    const colors=[
      '#22c55e',
      '#16a34a',
      '#facc15',
      '#f59e0b',
      '#3b82f6',
      '#60a5fa',
      '#ec4899',
      '#a78bfa',
      '#06b6d4',
      '#ffffff'
    ];

    /* Central celebration burst */
    const burst=document.createElement('div');
    burst.className='ed-celebration-burst';
    layer.appendChild(burst);

    const ring=document.createElement('div');
    ring.className='ed-celebration-ring';
    burst.appendChild(ring);

    for(let i=0;i<24;i++){
      const spark=document.createElement('span');

      spark.className='ed-burst-spark';

      const angle=(Math.PI*2*i)/24;
      const distance=65+Math.random()*105;

      spark.style.setProperty(
        '--bx',
        `${Math.cos(angle)*distance}px`
      );

      spark.style.setProperty(
        '--by',
        `${Math.sin(angle)*distance}px`
      );

      spark.style.background=colors[i%colors.length];
      spark.style.color=colors[i%colors.length];

      spark.style.animationDelay=
        `${Math.random()*90}ms`;

      burst.appendChild(spark);
    }

    /* Falling celebration */
    const mobile=window.innerWidth<600;
    const count=mobile?78:125;

    for(let i=0;i<count;i++){
      const piece=document.createElement('span');
      const kind=i%3;

      piece.className=
        'ed-confetti'+
        (kind===1?' round':kind===2?' ribbon':'');

      piece.style.left=
        `${Math.random()*100}%`;

      piece.style.background=
        colors[i%colors.length];

      piece.style.setProperty(
        '--dur',
        `${2.6+Math.random()*1.9}s`
      );

      piece.style.setProperty(
        '--delay',
        `${Math.random()*.32}s`
      );

      piece.style.setProperty(
        '--x1',
        `${-120+Math.random()*240}px`
      );

      piece.style.setProperty(
        '--x2',
        `${-180+Math.random()*360}px`
      );

      piece.style.setProperty(
        '--x3',
        `${-260+Math.random()*520}px`
      );

      piece.style.setProperty(
        '--r1',
        `${-360+Math.random()*720}deg`
      );

      piece.style.setProperty(
        '--r2',
        `${-720+Math.random()*1440}deg`
      );

      piece.style.setProperty(
        '--r3',
        `${-1080+Math.random()*2160}deg`
      );

      layer.appendChild(piece);
    }

    document.body.appendChild(layer);

    /* Tiny delayed sparkle pulse */
    setTimeout(()=>{
      const flash=document.createElement('div');
      flash.className='ed-celebration-flash';

      document.body.appendChild(flash);

      setTimeout(
        ()=>flash.remove(),
        750
      );
    },90);

    setTimeout(
      ()=>layer.remove(),
      5100
    );
  }

  function watch(){
    const box=document.getElementById('quizResult');

    if(!box){
      setTimeout(watch,250);
      return;
    }

    let wasVisible=
      !box.hidden &&
      !!box.innerHTML.trim();

    const observer=new MutationObserver(()=>{
      const visible=
        !box.hidden &&
        !!box.innerHTML.trim();

      /*
       * Celebration triggers only when the result becomes visible.
       * It NEVER changes the result element itself.
       */
      if(visible && !wasVisible){
        celebrate();
      }

      wasVisible=visible;
    });

    observer.observe(box,{
      attributes:true,
      attributeFilter:['hidden'],
      childList:true,
      subtree:true
    });
  }

  if(document.readyState==='loading'){
    document.addEventListener(
      'DOMContentLoaded',
      watch,
      {once:true}
    );
  }else{
    watch();
  }
})();
