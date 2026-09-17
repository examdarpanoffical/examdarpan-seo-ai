(function(){
  if(location.pathname.replace(/\/+$/,'')!=='/quiz') return;

  const style=document.createElement('style');
  style.textContent=`
    .ed-celebration-layer{
      position:fixed;
      inset:0;
      pointer-events:none;
      overflow:hidden;
      z-index:9999;
    }

    .ed-balloon{
      position:absolute;
      bottom:-90px;
      width:28px;
      height:36px;
      border-radius:50% 50% 45% 45%;
      opacity:0;
      animation:edBalloonRise 3s cubic-bezier(.2,.75,.25,1) forwards;
    }

    .ed-balloon:after{
      content:"";
      position:absolute;
      left:50%;
      top:100%;
      width:1px;
      height:65px;
      background:rgba(71,85,105,.4);
      transform:translateX(-50%);
    }

    .ed-balloon:before{
      content:"";
      position:absolute;
      left:50%;
      bottom:-4px;
      width:7px;
      height:7px;
      background:inherit;
      transform:translateX(-50%) rotate(45deg);
    }

    @keyframes edBalloonRise{
      0%{
        transform:translate3d(0,0,0) rotate(-5deg) scale(.75);
        opacity:0;
      }
      12%{opacity:.95}
      55%{
        transform:translate3d(18px,-55vh,0) rotate(7deg) scale(1);
        opacity:1;
      }
      100%{
        transform:translate3d(-14px,-112vh,0) rotate(-8deg) scale(.9);
        opacity:0;
      }
    }

    .ed-result-pop{
      animation:edResultPop .55s cubic-bezier(.2,.85,.25,1.15);
    }

    @keyframes edResultPop{
      0%{
        opacity:0;
        transform:translateY(18px) scale(.985);
      }
      70%{
        transform:translateY(-3px) scale(1.01);
      }
      100%{
        opacity:1;
        transform:none;
      }
    }

    @media(prefers-reduced-motion:reduce){
      .ed-balloon{
        animation:none!important;
        display:none;
      }
      .ed-result-pop{
        animation:none!important;
      }
    }
  `;
  document.head.appendChild(style);

  let celebrated=false;

  function celebrate(){
    if(celebrated) return;
    celebrated=true;

    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const layer=document.createElement('div');
    layer.className='ed-celebration-layer';

    const count=window.innerWidth<600 ? 14 : 24;

    for(let i=0;i<count;i++){
      const b=document.createElement('span');
      b.className='ed-balloon';

      b.style.left=`${5+Math.random()*90}%`;
      b.style.animationDelay=`${Math.random()*.4}s`;
      b.style.background=`hsl(${Math.round((i*137.5)%360)} 82% 58%)`;

      layer.appendChild(b);
    }

    document.body.appendChild(layer);
    setTimeout(()=>layer.remove(),3800);
  }

  function showResult(){
    const box=document.getElementById('quizResult');
    if(!box || box.hidden || !box.innerHTML.trim()) return;

    celebrate();

    box.classList.remove('ed-result-pop');
    void box.offsetWidth;
    box.classList.add('ed-result-pop');

    setTimeout(()=>{
      const y=box.getBoundingClientRect().top+window.scrollY-18;
      window.scrollTo({
        top:Math.max(0,y),
        behavior:'smooth'
      });
    },80);
  }

  function watch(){
    const box=document.getElementById('quizResult');
    if(!box){
      setTimeout(watch,250);
      return;
    }

    const observer=new MutationObserver(()=>{
      if(!box.hidden && box.innerHTML.trim()){
        showResult();
      }
    });

    observer.observe(box,{
      attributes:true,
      attributeFilter:['hidden'],
      childList:true,
      subtree:true
    });
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',watch);
  }else{
    watch();
  }
})();
