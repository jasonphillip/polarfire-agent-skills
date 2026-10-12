import numpy as np, tensorflow as tf, sys
out=sys.argv[1]; rng=np.random.RandomState(7)
W1=rng.normal(0,0.3,(64,32)).astype('float32'); b1=rng.normal(0,0.1,32).astype('float32'); W3=rng.normal(0,0.3,(32,1)).astype('float32'); b3=np.zeros(1,'float32')
X=rng.uniform(-1,1,(256,64)).astype('float32')
for name,act in (("G_fc_relu_fc","relu"),("H_fc_fc",None)):
    i=tf.keras.Input((64,),batch_size=1); d=tf.keras.layers.Dense(32,activation=act); f=tf.keras.layers.Dense(1); m=tf.keras.Model(i,f(d(i))); d.set_weights([W1,b1]); f.set_weights([W3,b3])
    def rep():
        for k in range(100): yield [X[k:k+1]]
    c=tf.lite.TFLiteConverter.from_keras_model(m); c.optimizations=[tf.lite.Optimize.DEFAULT]; c.representative_dataset=rep; c.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS_INT8]; c.inference_input_type=tf.int8; c.inference_output_type=tf.int8
    tfl=c.convert(); open(f"{out}/{name}.tflite","wb").write(tfl); it=tf.lite.Interpreter(model_content=tfl); it.allocate_tensors(); di=it.get_input_details()[0]; do=it.get_output_details()[0]
    sc,zp=di['quantization']; q=np.clip(np.rint(X[:4]/sc+zp),-128,127).astype(np.int8); outs=[]
    for k in range(4): it.set_tensor(di['index'],q[k:k+1]); it.invoke(); outs.append(it.get_tensor(do['index']).ravel().astype(int).tolist())
    np.save(f"{out}/{name}.q.npy",q); np.save(f"{out}/{name}.tflite_out.npy",np.array(outs,dtype=np.int8)); print(name,"tflite_raw",[o[:3] for o in outs])
