package de.nanoimaging.uc2controler;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

/**
 * Created by bene on 11.09.19.
 */



public class MyView extends View {

    public interface OnToggledListener {
        void OnToggled(MyView v, boolean touchOn);
    }

    boolean touchOn;
    boolean mDownTouch = false;
    private OnToggledListener toggledListener;
    int idX = 0; //default
    int idY = 0; //default

    public MyView(Context context, int x, int y) {
        super(context);
        idX = x;
        idY = y;
        init();
    }

    public MyView(Context context) {
        super(context);
        init();
    }

    public MyView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public MyView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        touchOn = false;
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        setMeasuredDimension(MeasureSpec.getSize(widthMeasureSpec),
                MeasureSpec.getSize(heightMeasureSpec));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        if (touchOn) {
            canvas.drawColor(Color.RED);
        } else {
            canvas.drawColor(Color.GRAY);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        super.onTouchEvent(event);

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:

                touchOn = !touchOn;
                invalidate();

                if(toggledListener != null){
                    toggledListener.OnToggled(this, touchOn);
                }

                mDownTouch = true;
                return true;

            case MotionEvent.ACTION_UP:
                if (mDownTouch) {
                    mDownTouch = false;
                    performClick();
                    return true;
                }
        }
        return false;
    }

    @Override
    public boolean performClick() {
        super.performClick();
        return true;
    }

    public void setOnToggledListener(OnToggledListener listener){
        toggledListener = listener;
    }

    public int getIdX(){
        return idX;
    }

    public int getIdY(){
        return idY;
    }

}
